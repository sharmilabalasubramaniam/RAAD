import React, { useState, useEffect } from 'react';
import { Download, ShieldCheck, History } from 'lucide-react';
import { apiService } from '../services/api';
import type { ReportCard } from '../types';

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<ReportCard[]>([]);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);

  useEffect(() => {
    apiService.getReports().then(setReports);
    apiService.getAuditEvents().then(setAuditEvents);
  }, []);

  const handleExportReport = (title: string, format: string) => {
    alert(`Generating and downloading ${title} in ${format} format...`);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 font-serif tracking-tight">
          Workforce Intelligence Reports
        </h1>
        <p className="text-xs text-slate-600 mt-1">
          Exportable compliance, SLA exposure, capacity audit, and skill gap reports for executive stakeholders.
        </p>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((report) => (
          <div key={report.id} className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                  {report.category}
                </span>
                <span className="text-[10px] font-mono font-bold bg-amber-100 text-amber-900 px-2 py-0.5 rounded">
                  {report.format}
                </span>
              </div>

              <h3 className="text-lg font-bold font-serif text-slate-900 leading-snug">{report.title}</h3>
              <p className="text-xs text-slate-600">{report.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono text-[11px]">Last generated: {report.lastGenerated}</span>

              <button
                onClick={() => handleExportReport(report.title, report.format)}
                className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export {report.format}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Audit Log Section */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-slate-700" />
            <h2 className="text-xl font-bold font-serif text-slate-900">
              Audit Trail & Governance Log
            </h2>
          </div>
          <span className="text-[10px] font-mono uppercase font-bold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> SOC2 Compliant Log
          </span>
        </div>

        <p className="text-xs text-slate-600">
          Immutable audit record of all automated and manual task reallocations, employee availability state changes, and capacity optimizations.
        </p>

        <div className="border border-slate-200 rounded-xl overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[10px] font-mono uppercase text-slate-500 font-bold">
                <th className="py-2.5 px-4">TIMESTAMP</th>
                <th className="py-2.5 px-4">ACTION</th>
                <th className="py-2.5 px-4">TASK / ENTITY</th>
                <th className="py-2.5 px-4">ORIGINAL ASSIGNEE</th>
                <th className="py-2.5 px-4">NEW ASSIGNEE</th>
                <th className="py-2.5 px-4">REASON & TRIGGER</th>
                <th className="py-2.5 px-4">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {auditEvents.map((event, idx) => (
                <tr key={event.id || idx} className="hover:bg-slate-50/80">
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                    {event.timestamp}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      event.action === 'REALLOCATE' ? 'bg-amber-100 text-amber-900 border-amber-300' :
                      event.action === 'AVAILABILITY_CHANGE' ? 'bg-purple-100 text-purple-900 border-purple-300' :
                      'bg-blue-100 text-blue-900 border-blue-300'
                    }`}>
                      {event.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {event.task_title || (event.task_id ? `Task #${event.task_id}` : 'Employee State')}
                  </td>
                  <td className="py-3 px-4 text-slate-700 font-medium">
                    {event.previous_employee_name || '—'}
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {event.new_employee_name || '—'}
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    <span className="block">{event.reason || 'Workforce optimization'}</span>
                    {event.trigger && <span className="text-[10px] text-slate-400 block font-mono">Trigger: {event.trigger}</span>}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                      {event.status || 'Recorded'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

