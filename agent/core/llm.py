import json
import logging
import re
from typing import Dict, Any, List, Optional
from core.config import settings
from core.prompts import WORKFORCE_AGENT_SYSTEM_PROMPT

# Import tool functions and schemas
from tools.workforce_tools import (
    get_workforce_summary,
    search_workers_by_skill,
    get_worker_profile,
    WORKFORCE_TOOL_DEFINITIONS
)
from tools.allocation_tools import (
    list_unassigned_tasks,
    recommend_candidates_for_task,
    explain_worker_selection,
    get_worker_assigned_tasks,
    reassign_worker_tasks,
    allocate_worker_to_task,
    ALLOCATION_TOOL_DEFINITIONS
)
from tools.conflict_tools import (
    list_workforce_conflicts,
    identify_overloaded_workers,
    check_critical_task_capacity,
    detect_missing_skills,
    CONFLICT_TOOL_DEFINITIONS
)

logger = logging.getLogger("agent.llm")

# Combined tool definitions for Gemini
ALL_TOOL_DEFINITIONS = (
    WORKFORCE_TOOL_DEFINITIONS +
    ALLOCATION_TOOL_DEFINITIONS +
    CONFLICT_TOOL_DEFINITIONS
)

# Registry mapping tool name to async callable
TOOL_DISPATCHER = {
    "get_workforce_summary": get_workforce_summary,
    "search_workers_by_skill": search_workers_by_skill,
    "get_worker_profile": get_worker_profile,
    "list_unassigned_tasks": list_unassigned_tasks,
    "recommend_candidates_for_task": recommend_candidates_for_task,
    "explain_worker_selection": explain_worker_selection,
    "get_worker_assigned_tasks": get_worker_assigned_tasks,
    "reassign_worker_tasks": reassign_worker_tasks,
    "allocate_worker_to_task": allocate_worker_to_task,
    "list_workforce_conflicts": list_workforce_conflicts,
    "identify_overloaded_workers": identify_overloaded_workers,
    "check_critical_task_capacity": check_critical_task_capacity,
    "detect_missing_skills": detect_missing_skills,
}

class LLMService:
    @classmethod
    async def process_chat(cls, user_message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes a manager prompt using Google Gemini with function calling if an API key
        is configured, or seamlessly falls back to the deterministic local reasoning engine.
        """
        api_key = settings.GEMINI_API_KEY
        if api_key and api_key.strip() and api_key != "YOUR_GEMINI_API_KEY":
            try:
                return await cls._process_with_gemini(user_message, api_key)
            except Exception as e:
                logger.warning(f"Gemini API execution failed: {e}. Falling back to local reasoning dispatcher.")
                return await cls._process_with_local_rules(user_message, fallback_reason=str(e))
        else:
            return await cls._process_with_local_rules(user_message)

    @classmethod
    async def _process_with_gemini(cls, user_message: str, api_key: str) -> Dict[str, Any]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Initial call with function declarations
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=WORKFORCE_AGENT_SYSTEM_PROMPT,
                tools=[{"function_declarations": ALL_TOOL_DEFINITIONS}],
                temperature=0.1
            )
        )

        actions_taken = []
        tool_calls_recorded = []

        if response.function_calls:
            function_responses = []
            for call in response.function_calls:
                fn_name = call.name
                fn_args = dict(call.args) if call.args else {}
                tool_calls_recorded.append({
                    "id": f"call_{fn_name}",
                    "name": fn_name,
                    "arguments": fn_args
                })

                # Execute backend tool
                handler = TOOL_DISPATCHER.get(fn_name)
                if handler:
                    result = await handler(**fn_args)
                else:
                    result = {"error": f"Tool '{fn_name}' not found."}

                actions_taken.append({
                    "tool": fn_name,
                    "input": fn_args,
                    "output": result
                })

                function_responses.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result}
                    )
                )

            # Send all tool outputs back to Gemini for final synthesis
            follow_up = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    user_message,
                    response.candidates[0].content,
                    *function_responses
                ],
                config=types.GenerateContentConfig(
                    system_instruction=WORKFORCE_AGENT_SYSTEM_PROMPT,
                    temperature=0.1
                )
            )
            final_text = follow_up.text or "I have processed your operational request with the workforce tools."
        else:
            final_text = response.text or "How can I assist you with workforce allocation and planning?"

        return {
            "role": "assistant",
            "message": final_text,
            "tool_calls": tool_calls_recorded,
            "actions_taken": actions_taken
        }

    @classmethod
    async def _process_with_local_rules(cls, user_message: str, fallback_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Deterministic, zero-latency local fallback dispatcher.
        Guarantees instant, accurate answers for all standard manager commands
        by executing real backend tools and formatting the results.
        """
        lower = user_message.lower().strip()
        actions_taken = []
        tool_calls = []

        # 1. Overloaded workers
        if any(w in lower for w in ["overloaded", "overbooked", "burnout", "exceeding capacity"]):
            tool_res = await identify_overloaded_workers()
            tool_calls.append({"id": "call_overloaded", "name": "identify_overloaded_workers", "arguments": {}})
            actions_taken.append({"tool": "identify_overloaded_workers", "output": tool_res})

            overloaded = tool_res.get("overloaded_workers", [])
            at_risk = tool_res.get("at_risk_workers", [])

            if not overloaded and not at_risk:
                msg = "✅ **No employees are overloaded!** All active personnel are within their weekly hour commitments."
            else:
                lines = [f"⚠️ **Identified {len(overloaded)} overloaded employee(s) and {len(at_risk)} at risk:**\n"]
                for o in overloaded:
                    lines.append(
                        f"- **{o['name']}** ({o['role']} - {o['department']}): "
                        f"Allocated **{o['allocated_hours']} hrs/wk** vs **{o['max_capacity']} hrs** limit "
                        f"(**+{o['overage_hours']} hrs overbooked**, {o['utilization_rate']} utilization)."
                    )
                if at_risk:
                    lines.append("\n**At-Risk Staff (90-100% capacity):**")
                    for a in at_risk:
                        lines.append(f"- **{a['name']}** ({a['role']}): {a['allocated_hours']}/{a['max_capacity']} hrs ({a['utilization_rate']})")
                lines.append("\n💡 *Recommendation*: Reassign surplus hours using the allocation engine to prevent delivery bottlenecks.")
                msg = "\n".join(lines)

        # 2. Workforce summary & Available employees
        elif any(w in lower for w in ["workforce summary", "health summary", "headcount", "kpi", "overview", "available", "how many employees"]):
            tool_res = await get_workforce_summary()
            tool_calls.append({"id": "call_summary", "name": "get_workforce_summary", "arguments": {}})
            actions_taken.append({"tool": "get_workforce_summary", "output": tool_res})

            m = tool_res.get("metrics", {})
            if tool_res.get("success") and not m.get("error"):
                avail_count = m.get("underallocated_workers", 0) + (m.get("active_workers", 0) - m.get("overallocated_workers", 0))
                lines = [
                    f"📊 **ResourcePulse Workforce & Availability Report**\n",
                    f"- **Total Headcount**: {m.get('total_workers')} ({m.get('active_workers')} active)",
                    f"- **Available / Unblocked Engineers**: **{m.get('underallocated_workers')} under-capacity**, {m.get('active_workers')} total active",
                    f"- **Average Utilization**: **{m.get('avg_utilization_pct')}%**",
                    f"- **Over-allocated Staff**: {m.get('overallocated_workers')}",
                    f"- **Skills Tracked**: {m.get('total_skills_tracked')}\n",
                    f"**Department Breakdown**:"
                ]
                for d in m.get("departments", []):
                    lines.append(f"- **{d['department']}**: {d['utilization_pct']}% utilization ({d['total_allocated_hours']:.0f}/{d['total_capacity_hours']:.0f} hrs)")
                msg = "\n".join(lines)
            else:
                msg = f"⚠️ Could not retrieve workforce summary: {tool_res.get('error', 'Backend unreachable')}"

        # 3. Highest priority task assignment / Who should handle
        elif any(w in lower for w in ["highest priority", "who should handle", "priority task"]):
            tool_res = await check_critical_task_capacity()
            tool_calls.append({"id": "call_critical_cap", "name": "check_critical_task_capacity", "arguments": {}})
            actions_taken.append({"tool": "check_critical_task_capacity", "output": tool_res})

            assessments = tool_res.get("task_assessments", [])
            lines = [f"🎯 **Highest Priority Task Staffing Recommendations**:\n"]
            if assessments:
                for a in assessments[:3]:
                    status_str = f"Assigned to **{a.get('assigned_worker_name')}**" if a.get("is_assigned") else "⚠️ **Unassigned - Requires Staffing**"
                    lines.append(
                        f"- **{a['title']}** (Priority: **{a['priority']}** | Project: *{a['project_name']}*)\n"
                        f"  - **Status**: {status_str}\n"
                        f"  - **Commitment**: {a['needed_hours']} hrs/wk\n"
                        f"  - **Viable Candidate Matches**: {len(a['viable_candidates'])} engineers with matching skills"
                    )
            else:
                lines.append("No active critical/high priority tasks requiring allocation changes.")
            msg = "\n".join(lines)

        # 4. Tasks at risk / SLA Risk
        elif any(w in lower for w in ["at risk", "tasks at risk", "sla risk", "breach"]):
            tool_res = await list_workforce_conflicts(unresolved_only=True)
            tool_calls.append({"id": "call_conflicts", "name": "list_workforce_conflicts", "arguments": {"unresolved_only": True}})
            actions_taken.append({"tool": "list_workforce_conflicts", "output": tool_res})

            conflicts = tool_res.get("conflicts", [])
            if not conflicts:
                msg = "✅ **Zero tasks currently at SLA risk!** All active assignments adhere to capacity and deadline constraints."
            else:
                lines = [f"⚠️ **Detected {len(conflicts)} Task(s) & Allocations at Risk:**\n"]
                for c in conflicts[:10]: # Limit to top 10 for clean readable response
                    worker = c.get('worker_name') or 'Unassigned'
                    lines.append(f"- **{worker}** [{c.get('severity', 'Risk')}]: {c.get('details', 'Risk detected')}")
                if len(conflicts) > 10:
                    lines.append(f"\n*...and {len(conflicts) - 10} additional items.*")
                lines.append("\n💡 *Action*: Click Reallocate or run auto-optimization to eliminate risk exposure.")
                msg = "\n".join(lines)

        # 4. Absence impact: "[Name] is unavailable. What tasks are affected?"
        elif "unavailable" in lower or "affected" in lower or "on leave" in lower or "sick" in lower:
            # Extract target name (e.g. Rahul, Marcus, Sarah, Elena, etc.)
            name_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", user_message)
            target_name = name_match.group(1) if name_match else "Rahul"
            # Ignore common query words
            if target_name.lower() in ["who", "what", "show", "are", "do", "why", "reassign"]:
                target_name = "Rahul"

            tool_res = await get_worker_assigned_tasks(target_name)
            tool_calls.append({"id": "call_assigned_tasks", "name": "get_worker_assigned_tasks", "arguments": {"worker_name": target_name}})
            actions_taken.append({"tool": "get_worker_assigned_tasks", "output": tool_res})

            if not tool_res.get("worker_found"):
                msg = f"🔍 **Worker Search**: {tool_res.get('message')}\n\n*Note*: All factual data is verified directly against the workforce database."
            else:
                affected = tool_res.get("affected_tasks", [])
                if not affected:
                    msg = f"ℹ️ **{tool_res.get('worker_name')}** has no active task commitments. Zero projects are affected by their unavailability."
                else:
                    lines = [f"⚠️ **{tool_res.get('worker_name')} is allocated to {len(affected)} active task(s):**\n"]
                    for t in affected:
                        lines.append(
                            f"- **{t['title']}** (Project: *{t['project_name']}*)\n"
                            f"  - **Priority**: {t['priority']} | **Hours**: {t['allocated_hours_per_week']} hrs/wk\n"
                            f"  - **Timeline**: {t['timeline']}"
                        )
                    lines.append(f"\n💡 *Next Step*: Say **'Reassign {tool_res.get('worker_name')}'s tasks'** to identify replacement candidates.")
                    msg = "\n".join(lines)

        # 5. Reassign tasks: "Reassign [Name]'s tasks"
        elif "reassign" in lower:
            name_match = re.search(r"reassign\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", user_message, re.IGNORECASE)
            target_name = name_match.group(1).strip() if name_match else "Rahul"

            tool_res = await reassign_worker_tasks(target_name, execute=False)
            tool_calls.append({"id": "call_reassign", "name": "reassign_worker_tasks", "arguments": {"worker_name": target_name, "execute": False}})
            actions_taken.append({"tool": "reassign_worker_tasks", "output": tool_res})

            if not tool_res.get("worker_found", True):
                msg = f"🔍 **Reassignment Error**: {tool_res.get('message')}"
            else:
                reassignments = tool_res.get("reassignments", [])
                if not reassignments:
                    msg = f"ℹ️ {tool_res.get('message', 'No active tasks found to reassign.')}"
                else:
                    lines = [f"🔄 **Proposed Reassignment Plan for {tool_res.get('worker_name')}'s tasks:**\n"]
                    for r in reassignments:
                        rec = r.get("recommended_worker")
                        if rec:
                            lines.append(
                                f"- **Task**: *{r['task_title']}* ({r['required_hours']} hrs/wk)\n"
                                f"  - **Recommended Replacement**: **{rec['name']}** (Fit Score: **{rec['match_score']}%**)\n"
                                f"  - **Available Bandwidth**: {rec['available_hours']} hrs/wk\n"
                                f"  - **Assessment**: {rec['fit_summary']}"
                            )
                        else:
                            lines.append(f"- **Task**: *{r['task_title']}* ⚠️ {r.get('warning')}")
                    lines.append("\n*To execute these assignments, confirm with 'Confirm reassignment'.*")
                    msg = "\n".join(lines)

        # 6. Candidate recommendation: "Who can handle this task?"
        elif any(w in lower for w in ["who can handle", "recommend candidate", "staff this task"]):
            # Look for UUID or task ID in query, or fetch first unassigned task
            uuid_match = re.search(r"([0-9a-fA-F-]{36})", user_message)
            task_id = uuid_match.group(1) if uuid_match else None

            if not task_id:
                unassigned_res = await list_unassigned_tasks()
                tasks = unassigned_res.get("unassigned_tasks", [])
                if tasks:
                    task_id = tasks[0]["task_id"]
                    task_title = tasks[0]["title"]
                else:
                    task_id = None
                    task_title = None

            if not task_id:
                msg = "ℹ️ No unassigned tasks found to evaluate. Provide a task ID: 'Who can handle task <task_id>'."
            else:
                tool_res = await recommend_candidates_for_task(task_id, limit=3)
                tool_calls.append({"id": "call_recommend", "name": "recommend_candidates_for_task", "arguments": {"task_id": task_id}})
                actions_taken.append({"tool": "recommend_candidates_for_task", "output": tool_res})

                recs = tool_res.get("recommendations", {})
                candidates = recs.get("top_candidates", [])

                lines = [f"🎯 **Top Candidate Recommendations for '{recs.get('task_title', 'Task')}'**:\n"]
                for i, c in enumerate(candidates, 1):
                    w = c["worker"]
                    bd = c["breakdown"]
                    lines.append(
                        f"**{i}. {w['name']}** - **{c['match_score']}% Match** ({w['role']})\n"
                        f"   - **Score Breakdown**: Skills {bd['skill_score']}% | Bandwidth {bd['availability_score']}% | Seniority {bd['experience_score']}%\n"
                        f"   - **Free Bandwidth**: {c['available_hours_per_week']} hrs/wk (Current Utilization: {w['utilization_rate']}%)\n"
                        f"   - **Assessment**: {c['fit_summary']}"
                    )
                    if c.get("potential_conflicts"):
                        lines.append(f"   - ⚠️ *Conflict Alert*: {', '.join(c['potential_conflicts'])}")
                msg = "\n".join(lines)

        # 7. Selection explanation: "Why was this worker selected?"
        elif "why" in lower and ("selected" in lower or "chosen" in lower or "recommended" in lower):
            # Check for worker name in message
            name_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", user_message)
            worker_name = name_match.group(1) if name_match else "Marcus"

            # Check unassigned tasks to pick a reference task
            unassigned_res = await list_unassigned_tasks()
            tasks = unassigned_res.get("unassigned_tasks", [])
            task_id = tasks[0]["task_id"] if tasks else "sample_task"

            tool_res = await explain_worker_selection(task_id, worker_name)
            tool_calls.append({"id": "call_explain", "name": "explain_worker_selection", "arguments": {"task_id": task_id, "worker_name": worker_name}})
            actions_taken.append({"tool": "explain_worker_selection", "output": tool_res})

            if not tool_res.get("success"):
                msg = f"🔍 {tool_res.get('message')}"
            else:
                bd = tool_res.get("breakdown", {})
                msg = (
                    f"🧐 **Allocation Engine Rationale for {tool_res.get('worker_name')}**:\n\n"
                    f"- **Overall Match Score**: **{tool_res.get('match_score')}%**\n"
                    f"- **Skills Fit**: **{bd.get('skill_score')}%** (Verified competency against task requirements)\n"
                    f"- **Availability Fit**: **{bd.get('availability_score')}%** ({tool_res.get('available_hours')} free weekly hours)\n"
                    f"- **Seniority Alignment**: **{bd.get('experience_score')}%** (Matches task priority weighting)\n\n"
                    f"**Summary**: {tool_res.get('fit_summary')}"
                )

        # 8. Workforce conflicts
        elif any(w in lower for w in ["conflicts", "workforce conflicts", "clashes", "leave clashes"]):
            tool_res = await list_workforce_conflicts(unresolved_only=True)
            tool_calls.append({"id": "call_conflicts", "name": "list_workforce_conflicts", "arguments": {"unresolved_only": True}})
            actions_taken.append({"tool": "list_workforce_conflicts", "output": tool_res})

            conflicts = tool_res.get("conflicts", [])
            if not conflicts:
                msg = "✅ **Zero workforce conflicts detected!** All assignments adhere to weekly working limits and leave schedules."
            else:
                lines = [f"⚠️ **Detected {len(conflicts)} active allocation conflict(s):**\n"]
                for c in conflicts:
                    lines.append(f"- **{c['worker_name']}** [{c['severity']} {c['type']}]: {c['details']}")
                lines.append("\n💡 *Action*: Propose reassignments to eliminate overbooking.")
                msg = "\n".join(lines)

        # 9. Critical tasks capacity
        elif "critical" in lower or "enough workforce" in lower:
            tool_res = await check_critical_task_capacity()
            tool_calls.append({"id": "call_critical_cap", "name": "check_critical_task_capacity", "arguments": {}})
            actions_taken.append({"tool": "check_critical_task_capacity", "output": tool_res})

            unstaffed = tool_res.get("unstaffed_critical_count", 0)
            total = tool_res.get("total_critical_high_tasks", 0)
            deficit = tool_res.get("has_capacity_deficit", False)

            lines = [
                f"🛡️ **Critical & High Priority Task Capacity Assessment**:\n",
                f"- **Tracked Priority Tasks**: {total}",
                f"- **Unstaffed Critical Tasks**: {unstaffed}",
                f"- **Capacity Deficit Status**: {'⚠️ **Deficit Detected**' if deficit else '✅ **Sufficient Talent Available**'}\n"
            ]
            for a in tool_res.get("task_assessments", []):
                status_icon = "✅" if a["is_assigned"] else "⏳"
                lines.append(f"- {status_icon} **{a['title']}** ({a['priority']} - {a['project_name']}): Needed {a['needed_hours']} hrs/wk | Viable candidates: {len(a['viable_candidates'])}")

            msg = "\n".join(lines)

        # 10. Missing skills
        elif any(w in lower for w in ["missing skills", "skill gap", "missing talent", "skills are missing"]):
            tool_res = await detect_missing_skills()
            tool_calls.append({"id": "call_missing_skills", "name": "detect_missing_skills", "arguments": {}})
            actions_taken.append({"tool": "detect_missing_skills", "output": tool_res})

            missing = tool_res.get("completely_missing_skills", [])
            gaps = tool_res.get("proficiency_gaps", [])

            if not missing and not gaps:
                msg = "✅ **No skill gaps found!** The current workforce possesses all required competencies at required proficiency levels."
            else:
                lines = [f"🔍 **Workforce Skill Deficit Analysis:**\n"]
                if missing:
                    lines.append(f"**Completely Missing Skills ({len(missing)}):**")
                    for m in missing:
                        lines.append(f"- **{m['skill_name']}** needed for *{m['task_title']}* ({m['project_name']}) - {m['reason']}")
                if gaps:
                    lines.append(f"\n**Proficiency Gaps ({len(gaps)}):**")
                    for g in gaps:
                        lines.append(f"- **{g['skill_name']}** for *{g['task_title']}*: {g['reason']}")
                msg = "\n".join(lines)

        else:
            # Default helpful assistant response
            msg = (
                "👋 Hello! I am your **ResourcePulse AI Workforce Operations Agent**.\n\n"
                "I communicate directly with the workforce backend to help you with:\n"
                "- 📊 **'Show workforce summary'**: KPIs, headcount, and departmental utilization\n"
                "- ⚠️ **'Who is overloaded?'**: Identify overbooked staff (>40h/wk)\n"
                "- 📋 **'Show unassigned tasks'**: Backlog tasks requiring personnel\n"
                "- 🎯 **'Who can handle this task?'**: Multi-factor candidate fit matching\n"
                "- 🧐 **'Why was this worker selected?'**: Transparent score breakdown\n"
                "- 🏥 **'Rahul is unavailable. What tasks are affected?'**: Evaluate absence impact\n"
                "- 🔄 **'Reassign Rahul's tasks'**: Autonomous candidate replacement plan\n"
                "- 🛡️ **'Do we have enough workforce for these critical tasks?'**: Capacity assessment\n"
                "- 🔍 **'What skills are missing?'**: Skill gap and proficiency deficit scan"
            )

        if fallback_reason:
            msg += f"\n\n*(Running in Local Agent Mode: {fallback_reason})*"

        return {
            "role": "assistant",
            "message": msg,
            "tool_calls": tool_calls,
            "actions_taken": actions_taken
        }
