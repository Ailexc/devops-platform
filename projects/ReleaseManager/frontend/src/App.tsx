import { useEffect } from 'react';
import AppRouter from './router';
import { useAuthStore } from './store/useAuthStore';

function App() {
  const loadUser = useAuthStore((s) => s.loadUser);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return <AppRouter />;
}

export default App;