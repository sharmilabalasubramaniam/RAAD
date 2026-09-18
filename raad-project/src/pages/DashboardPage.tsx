import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  Zap, 
  Layers, 
  AlertTriangle, 
  Download, 
  ChevronDown, 
  RotateCcw
} from 'lucide-react';
import { BottleneckAlert } from '../components/dashboard/BottleneckAlert';
import { WorkloadDistribution } from '../components/dashboard/WorkloadDistribution';
import { SlaHealthDonut } from '../components/dashboard/SlaHealthDonut';
import { ActiveWorkloadTable } from '../components/dashboard/ActiveWorkloadTable';
import { ReallocationModal } from '../components/reallocation/ReallocationModal';
import { apiService } from '../services/api';
import type { Employee, Task, SlaHealthSummary } from '../types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [slaHealth, setSlaHealth] = useState<SlaHealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showBottleneckAlert, setShowBottleneckAlert] = useState(true);
  const [isReallocationModalOpen, setIsReallocationModalOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [empData, taskData, slaData] = await Promise.all([
          apiService.getEmployees(),
          apiService.getTasks(),
          apiService.getSlaHealth()
        ]);
        setEmployees(empData);
        setTasks(taskData);
        setSlaHealth(slaData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleReallocateTask = (_task: Task) => {
    setIsReallocationModalOpen(true);
  };

  const handleViewTaskDetails = (task: Task) => {
    navigate(`/tasks?selected=${task.id}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-500 font-mono">Initializing RAAD Workforce Telemetry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      
      {/* Top Telemetry Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-slate-500">
              DECISION RUNTIME: ACTIVE
            </span>
            <span className="text-[10px] font-mono text-slate-400">|</span>
            <span className="text-[10px] font-mono text-slate-500 font-semibold">
              CLUSTER-ID: NORDIC-09
            </span>
          </div>

          <h1 className="text-3xl font-extrabold text-slate-900 font-serif tracking-tight">
            Workforce Command Center
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-3xl">
            AI-powered workforce intelligence and real-time precision allocation. Autonomous telemetry monitoring 32 active engineers across enterprise platforms.
          </p>
        </div>

        {/* Controls Toolbar */}
        <div className="flex items-center gap-2.5 flex-wrap self-start lg:self-center">
          <div className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 font-medium flex items-center gap-2 shadow-2xs">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            <span>Today, Oct 24 • Live Stream</span>
          </div>

          <button className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition flex items-center gap-2 shadow-2xs">
            <span>Engineering & Platform Ops</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          <button 
            onClick={() => setIsReallocationModalOpen(true)}
            className="bg-[#475569] hover:bg-slate-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Simulate Reallocation</span>
          </button>

          <button 
            onClick={() => alert('Exporting Workforce Telemetry Summary...')}
            className="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* 4 KPI CARDS GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* KPI 1: TOTAL WORKFORCE */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider">
                TOTAL WORKFORCE
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-extrabold text-slate-900 font-serif">32</span>
                <span className="text-xs text-slate-600 font-semibold">Engineers</span>
              </div>
            </div>
            <div className="p-2.5 bg-blue-50 text-blue-700 rounded-xl">
              <Users className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60">
              • 94% verified active
            </span>
            <span className="text-slate-500">2 on scheduled leave</span>
          </div>
        </div>

        {/* KPI 2: IMMEDIATE AVAILABILITY */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider">
                IMMEDIATE AVAILABILITY
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-extrabold text-slate-900 font-serif">24</span>
                <span className="text-xs text-slate-600 font-semibold">Available</span>
              </div>
            </div>
            <div className="p-2.5 bg-sky-50 text-sky-700 rounded-xl">
              <Zap className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="font-semibold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200/60">
              ➔ 75% unblocked capacity
            </span>
            <span className="text-slate-500 font-mono">192h total headroom</span>
          </div>
        </div>

        {/* KPI 3: ACTIVE TASKS */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider">
                ACTIVE TASKS
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-extrabold text-slate-900 font-serif">72</span>
                <span className="text-xs text-slate-600 font-semibold">In Flight</span>
              </div>
            </div>
            <div className="p-2.5 bg-slate-100 text-slate-700 rounded-xl">
              <Layers className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-600 font-medium">Across 6 sprint workstreams</span>
            <span className="font-mono text-slate-700 font-semibold">Avg: 2.2 / eng</span>
          </div>
        </div>

        {/* KPI 4: SLA EXPOSURE */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider">
                SLA EXPOSURE
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-extrabold text-rose-700 font-serif">8</span>
                <span className="text-xs text-slate-600 font-semibold">Tickets at Risk</span>
              </div>
            </div>
            <div className="p-2.5 bg-rose-50 text-rose-700 rounded-xl border border-rose-100">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="font-bold text-rose-800 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
              • 5 critical (&lt;4h)
            </span>
            <span className="text-amber-800 font-medium">3 approaching</span>
          </div>
        </div>

      </div>

      {/* BOTTLENECK DETECTION ALERT */}
      {showBottleneckAlert && (
        <BottleneckAlert
          onReviewRecommendation={() => navigate('/copilot')}
          onDismiss={() => setShowBottleneckAlert(false)}
        />
      )}

      {/* MIDDLE SECTION: WORKLOAD & SLA DONUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <WorkloadDistribution employees={employees} />
        </div>
        <div>
          {slaHealth && (
            <SlaHealthDonut 
              slaHealth={slaHealth} 
              onOpenCopilot={() => navigate('/copilot')} 
            />
          )}
        </div>
      </div>

      {/* BOTTOM SECTION: ACTIVE WORKLOAD ALLOCATIONS TABLE */}
      <ActiveWorkloadTable
        tasks={tasks}
        onReallocateTask={handleReallocateTask}
        onViewTaskDetails={handleViewTaskDetails}
      />

      <ReallocationModal
        isOpen={isReallocationModalOpen}
        onClose={() => setIsReallocationModalOpen(false)}
      />
    </div>
  );
};
