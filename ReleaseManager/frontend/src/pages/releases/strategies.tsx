import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ReleaseStrategiesPage() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate('/knowledge/docs', { replace: true });
  }, [navigate]);

  return null;
}
