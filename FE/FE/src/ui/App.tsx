import { Toaster } from 'sonner';
import { AppRouter } from './navigations/AppRouter.tsx';
import { AppProviders } from '../store/AppProviders.tsx';

export default function App() {
  return (
    <AppProviders>
      <AppRouter />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            border: '1px solid #334155',
            color: '#f8fafc',
            fontSize: '13px',
          },
          classNames: {
            success: '[&_[data-icon]]:text-emerald-400',
            error: '[&_[data-icon]]:text-red-400',
            title: '!text-slate-100',
            description: '!text-slate-400',
          },
        }}
      />
    </AppProviders>
  );
}
