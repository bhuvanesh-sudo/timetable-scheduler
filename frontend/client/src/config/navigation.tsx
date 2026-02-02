import { 
  LayoutDashboard, 
  UploadCloud, 
  CalendarDays, 
  BarChart3, 
  ShieldCheck
} from 'lucide-react';

export const NAV_ITEMS = [
  { 
    label: 'Dashboard', 
    path: '/dashboard', 
    icon: <LayoutDashboard size={20} />, 
    roles: ['ADMIN', 'HOD', 'FACULTY'] 
  },
  { 
    label: 'Data Import', 
    path: '/dashboard/upload', 
    icon: <UploadCloud size={20} />, 
    roles: ['ADMIN'] 
  },
  { 
    label: 'Master Schedule', 
    path: '/dashboard/schedule', 
    icon: <CalendarDays size={20} />, 
    roles: ['ADMIN', 'HOD'] 
  },
  { 
    label: 'Workload Pulse', 
    path: '/dashboard/analytics', 
    icon: <BarChart3 size={20} />, 
    roles: ['HOD', 'ADMIN'] 
  },
  { 
    label: 'System Health', 
    path: '/dashboard/health', 
    icon: <ShieldCheck size={20} />, 
    roles: ['ADMIN'] 
  },
];