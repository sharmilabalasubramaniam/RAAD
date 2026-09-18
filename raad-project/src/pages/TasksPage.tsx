import React, { useState, useEffect } from 'react';
import { Search, Filter, Clock, X } from 'lucide-react';
import { apiService } from '../services/api';
import type { Task } from '../types';

export const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  useEffect(() => {
    apiService.getTasks().then(setTasks);
  }, []);

  const filteredTasks = tasks.filter((t) => {
    const matchesSearch = 
      t.taskName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.taskCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.assignedEmployeeName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.workstream.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesPriority = priorityFilter === 'ALL' || t.priority === priorityFilter;

    return matchesSearch && matchesPriority;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'Critical':
        return 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
      case 'Urgent':
        return 'bg-amber-100 text-amber-900 border-amber-300 font-semibold';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200 font-medium';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 font-serif tracking-tight">
            Active Task Matrix & SLA Horizon
          </h1>
          <p className="text-xs text-slate-600 mt-1">
            72 sprint commitments monitored continuously for SLA breach risks and AI skill alignment.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="bg-rose-50 text-rose-800 border border-rose-200 px-3 py-1.5 rounded-lg font-bold">
            5 SLA Critical Breaches
          </span>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search task code, name, assignee..."
            className="w-full bg-slate-100/80 border border-slate-200 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            aria-label="Filter tasks by priority"
            className="bg-slate-100/80 border border-slate-200 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-700 focus:outline-none"
          >
            <option value="ALL">Priority: All</option>
            <option value="Critical">Critical</option>
            <option value="Urgent">Urgent</option>
            <option value="Standard">Standard</option>
          </select>
        </div>
      </div>

      {/* Task Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTasks.map((task) => (
          <div
            key={task.id}
            onClick={() => setSelectedTask(task)}
            className="bg-white border border-slate-200/90 hover:border-blue-400 rounded-2xl p-5 shadow-xs transition hover:shadow-md cursor-pointer flex flex-col justify-between space-y-4"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-slate-400">
                  {task.taskCode}
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${getPriorityBadge(task.priority)}`}>
                  {task.priority}
                </span>
              </div>

              <h3 className="text-sm font-bold text-slate-900 leading-snug">{task.taskName}</h3>
              <p className="text-xs text-slate-500">{task.workstream}</p>
            </div>

            <div className="pt-3 border-t border-slate-100 space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span className="text-slate-400 text-[11px]">Assignee:</span>
                <div className="flex items-center gap-1.5 font-medium text-slate-900">
                  <div className={`w-4 h-4 rounded-full ${task.assignedEmployeeAvatarColor} text-white text-[9px] font-bold flex items-center justify-center`}>
                    {task.assignedEmployeeInitials}
                  </div>
                  <span>{task.assignedEmployeeName}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-slate-600 font-mono text-[11px]">
                <span className="text-slate-400">Remaining SLA:</span>
                <span className="font-bold text-rose-700 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{task.remainingSla}</span>
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400">AI Skill Match:</span>
                <span className="font-bold text-amber-800 font-mono">{task.aiSkillMatch}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Task Modal Details */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono text-slate-400">{selectedTask.taskCode}</span>
                <h3 className="text-lg font-bold font-serif text-slate-900">{selectedTask.taskName}</h3>
              </div>
              <button onClick={() => setSelectedTask(null)} className="p-1 text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">{selectedTask.description}</p>

            <div className="bg-slate-50 p-4 rounded-xl space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Workstream:</span>
                <span className="font-semibold text-slate-800">{selectedTask.workstream}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Assignee:</span>
                <span className="font-semibold text-slate-800">{selectedTask.assignedEmployeeName}</span>
              </div>
              <div className="flex justify-between font-mono">
                <span className="text-slate-500">Remaining SLA:</span>
                <span className="font-bold text-rose-700">{selectedTask.remainingSla}</span>
              </div>
              <div className="flex justify-between font-mono">
                <span className="text-slate-500">AI Skill Fit:</span>
                <span className="font-bold text-amber-800">{selectedTask.aiSkillMatch}%</span>
              </div>
            </div>

            <button
              onClick={() => setSelectedTask(null)}
              className="w-full py-2 bg-slate-900 text-white text-xs font-semibold rounded-lg hover:bg-slate-800 transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
