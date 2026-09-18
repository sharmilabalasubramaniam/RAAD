import { 
  Employee, 
  Task, 
  Skill, 
  AlertItem, 
  SlaHealthSummary, 
  ReallocationPlanData, 
  ReportCard, 
  ForecastDataPoint,
  CopilotMessage 
} from '../types';
import { 
  mockEmployees, 
  mockTasks, 
  mockSkills, 
  mockSlaHealth, 
  mockReallocationPlan, 
  mockAlerts, 
  mockReportCards, 
  mockForecastData 
} from '../data/mockData';

// API Service Layer (Mock Implementation - Ready for REST/GraphQL backend connection)
class ApiService {
  private delay(ms: number = 200): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async getEmployees(): Promise<Employee[]> {
    await this.delay();
    return [...mockEmployees];
  }

  async getTasks(): Promise<Task[]> {
    await this.delay();
    return [...mockTasks];
  }

  async getSkills(): Promise<Skill[]> {
    await this.delay();
    return [...mockSkills];
  }

  async getSlaHealth(): Promise<SlaHealthSummary> {
    await this.delay();
    return { ...mockSlaHealth };
  }

  async getReallocationPlan(): Promise<ReallocationPlanData> {
    await this.delay();
    return { ...mockReallocationPlan };
  }

  async applyReallocation(planId: string): Promise<{ success: boolean; message: string }> {
    await this.delay(400);
    return {
      success: true,
      message: `Reallocation Plan ${planId} successfully executed across Nordic cluster. 4 tasks reallocated with zero predicted SLA breaches.`
    };
  }

  async getAlerts(): Promise<AlertItem[]> {
    await this.delay();
    return [...mockAlerts];
  }

  async getReports(): Promise<ReportCard[]> {
    await this.delay();
    return [...mockReportCards];
  }

  async getForecast(horizon: '7 Days' | '14 Days' | '30 Days'): Promise<ForecastDataPoint[]> {
    await this.delay();
    return mockForecastData[horizon] || mockForecastData['7 Days'];
  }

  async askCopilot(question: string): Promise<CopilotMessage> {
    await this.delay(600);
    
    const lower = question.toLowerCase();
    
    if (lower.includes('overload') || lower.includes('capacity') || lower.includes('rahul')) {
      return {
        id: `msg-${Date.now()}`,
        sender: 'assistant',
        text: 'I analyzed Rahul Sharma\'s active queue and identified 4 affected tasks at immediate risk. Total projected unmitigated risk: $42,000 SLA penalty exposure within a 14h critical window.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        planData: mockReallocationPlan
      };
    }

    if (lower.includes('ticket') || lower.includes('sla') || lower.includes('risk')) {
      return {
        id: `msg-${Date.now()}`,
        sender: 'assistant',
        text: 'ANSWER:\nCurrently 8 tickets are exposed to SLA risks. 5 critical (<4h remaining) and 3 approaching breaches.\n\nWHY:\nPlatform Engineering has a high task density (2.2 tasks/engineer) while 2 engineers are on scheduled leave.\n\nEVIDENCE:\nTicket #104 (Distributed Cache) has 3h 15m remaining assigned to Rahul (95% load).\n\nRECOMMENDED ACTION:\nExecute RAAD Reallocation Plan #RP-8021 to shift tasks to Arun Kumar & Priya Sundaram.\n\nIMPACT:\nSLA Compliance increases from 81.9% to 98.6% with zero breaches.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
    }

    if (lower.includes('skill') || lower.includes('gap')) {
      return {
        id: `msg-${Date.now()}`,
        sender: 'assistant',
        text: 'ANSWER:\nPrimary skill gap detected in Kubernetes Ingress Controller Failover & Go Runtime Latency Tuning.\n\nWHY:\nOnly 2 engineers hold >90% proficiency in distributed system failovers for Nordic region.\n\nEVIDENCE:\nNordic Cluster ID NORDIC-09 telemetry shows 14% skill deficit on security mTLS mesh.\n\nRECOMMENDED ACTION:\nInitiate cross-training pod with Priya Sundaram leading Go optimization workshops.\n\nIMPACT:\nEliminates single-point-of-failure dependencies on emergency callouts.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
    }

    return {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: `ANSWER:\nAnalyzed workforce telemetry across all 32 active engineers for prompt: "${question}".\n\nWHY:\nRAAD Engine v4.2 telemetry indicates optimal system health with 24 available headcount.\n\nEVIDENCE:\nSystem latency is 120ms with 98.4% allocation confidence.\n\nRECOMMENDED ACTION:\nReview active workload allocations table or run a capacity simulation.\n\nIMPACT:\nMaintains 75% unblocked headroom across Nordic Enterprise Ops.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  }
}

export const apiService = new ApiService();
