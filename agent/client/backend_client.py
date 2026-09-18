import logging
from typing import List, Dict, Any, Optional
import httpx
from core.config import settings

logger = logging.getLogger("agent.backend_client")

class BackendClient:
    """
    Asynchronous HTTP client communicating exclusively with the Workforce Backend
    via REST APIs. Does not access the backend database directly.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.BACKEND_URL).rstrip("/")
        self.timeout = timeout or settings.TIMEOUT_SECONDS

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Backend HTTP error {e.response.status_code} for {url}: {e.response.text}")
                return {
                    "error": True,
                    "status_code": e.response.status_code,
                    "detail": e.response.text
                }
            except httpx.RequestError as e:
                logger.error(f"Backend connection error for {url}: {e}")
                return {
                    "error": True,
                    "status_code": 503,
                    "detail": f"Failed to connect to workforce backend at {self.base_url}: {str(e)}"
                }

    async def check_health(self) -> Dict[str, Any]:
        """Check backend server health."""
        # Backend health is at host root /health
        host_root = self.base_url.split("/api")[0] if "/api" in self.base_url else self.base_url
        url = f"{host_root}/health"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.get(url)
                return {"connected": res.status_code == 200, "data": res.json()}
            except Exception as e:
                return {"connected": False, "error": str(e)}

    # ---------------------------------------------------------
    # Workforce Endpoints
    # ---------------------------------------------------------
    async def get_workforce_metrics(self) -> Dict[str, Any]:
        """GET /workforce/metrics"""
        return await self._request("GET", "/workforce/metrics")

    async def get_workers(
        self,
        department: Optional[str] = None,
        skill: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """GET /workforce/workers"""
        params = {"is_active": is_active}
        if department:
            params["department"] = department
        if skill:
            params["skill"] = skill
        res = await self._request("GET", "/workforce/workers", params=params)
        return res if isinstance(res, list) else []

    async def get_worker_by_id(self, worker_id: str) -> Dict[str, Any]:
        """GET /workforce/workers/{worker_id}"""
        return await self._request("GET", f"/workforce/workers/{worker_id}")

    async def get_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """GET /workforce/skills"""
        params = {"category": category} if category else {}
        res = await self._request("GET", "/workforce/skills", params=params)
        return res if isinstance(res, list) else []

    # ---------------------------------------------------------
    # Allocation & Project Endpoints
    # ---------------------------------------------------------
    async def get_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """GET /allocation/projects"""
        params = {"status": status} if status else {}
        res = await self._request("GET", "/allocation/projects", params=params)
        return res if isinstance(res, list) else []

    async def get_project_detail(self, project_id: str) -> Dict[str, Any]:
        """GET /allocation/projects/{project_id}"""
        return await self._request("GET", f"/allocation/projects/{project_id}")

    async def get_task_recommendations(self, task_id: str, limit: int = 5) -> Dict[str, Any]:
        """GET /allocation/tasks/{task_id}/recommendations"""
        return await self._request("GET", f"/allocation/tasks/{task_id}/recommendations", params={"limit": limit})

    async def allocate_worker(
        self,
        task_id: str,
        worker_id: str,
        allocated_hours_per_week: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """POST /allocation/allocate"""
        payload = {
            "task_id": task_id,
            "worker_id": worker_id,
            "allocated_hours_per_week": allocated_hours_per_week or 20.0,
            "start_date": "2026-01-01",  # Placeholder required by schema, optimizer uses task dates
            "end_date": "2026-12-31",
            "notes": notes
        }
        return await self._request("POST", "/allocation/allocate", json=payload)

    async def auto_optimize(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """POST /allocation/auto-optimize"""
        params = {"project_id": project_id} if project_id else {}
        res = await self._request("POST", "/allocation/auto-optimize", params=params)
        return res if isinstance(res, list) else []

    async def get_conflicts(self, unresolved_only: bool = True) -> List[Dict[str, Any]]:
        """GET /allocation/conflicts"""
        res = await self._request("GET", "/allocation/conflicts", params={"unresolved_only": unresolved_only})
        return res if isinstance(res, list) else []

    # ---------------------------------------------------------
    # Copilot Tool Execution Reuse
    # ---------------------------------------------------------
    async def execute_copilot_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """POST /copilot/execute-tool"""
        payload = {"tool_name": tool_name, "parameters": parameters}
        return await self._request("POST", "/copilot/execute-tool", json=payload)

    # ---------------------------------------------------------
    # High-level Aggregation Helpers
    # ---------------------------------------------------------
    async def find_worker_by_name(self, name_query: str) -> Optional[Dict[str, Any]]:
        """Find a worker by name (case-insensitive substring or exact match)."""
        workers = await self.get_workers()
        query = name_query.strip().lower()
        # Exact match first
        for w in workers:
            if w.get("name", "").lower() == query:
                return w
        # Substring / first name match
        for w in workers:
            if query in w.get("name", "").lower():
                return w
        return None

    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Fetch all tasks across all projects with project metadata."""
        projects = await self.get_projects()
        all_tasks = []
        for p in projects:
            p_id = p.get("id")
            if not p_id:
                continue
            detail = await self.get_project_detail(p_id)
            for t in detail.get("tasks", []):
                t_copy = dict(t)
                t_copy["project_name"] = p.get("name")
                t_copy["project_code"] = p.get("code")
                all_tasks.append(t_copy)
        return all_tasks

backend_client = BackendClient()
