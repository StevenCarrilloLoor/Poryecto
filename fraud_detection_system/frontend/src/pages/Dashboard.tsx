// frontend/src/pages/Dashboard.tsx

import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Skeleton,
  Tooltip,
  Paper,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Assessment,
  Security,
  Speed,
  AccountBalance,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';

import { useWebSocket } from '../context/WebSocketContext';
import { api } from '../services/api';
import RecentFraudCases from '../components/Dashboard/RecentFraudCases';
import LiveActivityFeed from '../components/Dashboard/LiveActivityFeed';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

interface DashboardMetrics {
  totalCases: number;
  totalAmount: number;
  avgConfidence: number;
  pendingCases: number;
  confirmedCases: number;
  falsePositives: number;
  criticalCases: number;
  todayCases: number;
  weekTrend: number;
  monthTrend: number;
  detectionRate: number;
  responseTime: number;
}

interface ChartData {
  labels: string[];
  datasets: any[];
}

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const { isConnected, lastMessage } = useWebSocket();
  const [realTimeAlert, setRealTimeAlert] = useState<any>(null);

  // Fetch dashboard metrics
  const { data: metrics, isLoading: metricsLoading, refetch } = useQuery({
    queryKey: ['dashboardMetrics'],
    queryFn: () => api.get('/dashboard/metrics'),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch chart data
  const { data: chartData, isLoading: chartLoading } = useQuery({
    queryKey: ['dashboardCharts'],
    queryFn: () => api.get('/dashboard/charts'),
  });

  // Handle real-time updates
  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage);
      if (data.type === 'fraud_alert') {
        setRealTimeAlert(data.payload);
        setTimeout(() => setRealTimeAlert(null), 10000);
      }
    }
  }, [lastMessage]);

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
  }> = ({ title, value, change, icon, color, subtitle }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card
        sx={{
          background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(
            color,
            0.05
          )} 100%)`,
          border: `1px solid ${alpha(color, 0.2)}`,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: `linear-gradient(90deg, ${color}, ${alpha(color, 0.3)})`,
          },
        }}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {title}
              </Typography>
              <Typography variant="h4" fontWeight="bold" color={color}>
                {value}
              </Typography>
              {subtitle && (
                <Typography variant="caption" color="text.secondary">
                  {subtitle}
                </Typography>
              )}
              {change !== undefined && (
                <Box display="flex" alignItems="center" mt={1}>
                  {change > 0 ? (
                    <TrendingUp fontSize="small" color="success" />
                  ) : (
                    <TrendingDown fontSize="small" color="error" />
                  )}
                  <Typography
                    variant="body2"
                    color={change > 0 ? 'success.main' : 'error.main'}
                    ml={0.5}
                  >
                    {Math.abs(change)}%
                  </Typography>
                </Box>
              )}
            </Box>
            <Box
              sx={{
                backgroundColor: alpha(color, 0.1),
                borderRadius: 2,
                p: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );

  const severityDistributionData = {
    labels: ['Bajo', 'Medio', 'Alto', 'Crítico'],
    datasets: [
      {
        data: chartData?.severityDistribution || [30, 25, 35, 10],
        backgroundColor: [
          theme.palette.success.main,
          theme.palette.warning.main,
          theme.palette.error.main,
          theme.palette.error.dark,
        ],
        borderWidth: 0,
      },
    ],
  };

  const trendChartData = {
    labels: chartData?.trendLabels || ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
    datasets: [
      {
        label: 'Casos Detectados',
        data: chartData?.trendData || [12, 19, 15, 25, 22, 30, 28],
        borderColor: theme.palette.primary.main,
        backgroundColor: alpha(theme.palette.primary.main, 0.1),
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Casos Confirmados',
        data: chartData?.confirmedTrendData || [8, 12, 10, 18, 15, 22, 20],
        borderColor: theme.palette.success.main,
        backgroundColor: alpha(theme.palette.success.main, 0.1),
        tension: 0.4,
        fill: true,
      },
    ],
  };

  return (
    <Box>
      {/* Real-time Alert */}
      {realTimeAlert && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
        >
          <Alert
            severity="warning"
            icon={<Warning />}
            sx={{ mb: 3 }}
            onClose={() => setRealTimeAlert(null)}
          >
            <strong>Nueva Alerta de Fraude:</strong> {realTimeAlert.description} - 
            Severidad: {realTimeAlert.severity}
          </Alert>
        </motion.div>
      )}

      {/* Header */}
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" fontWeight="bold">
            Panel de Control de Fraudes
          </Typography>
          <Box display="flex" gap={2}>
            <Chip
              icon={isConnected ? <CheckCircle /> : <Error />}
              label={isConnected ? 'Conectado' : 'Desconectado'}
              color={isConnected ? 'success' : 'error'}
              variant="outlined"
            />
            <IconButton onClick={() => refetch()} color="primary">
              <Refresh />
            </IconButton>
          </Box>
        </Box>
      </Box>

      {/* Metrics Grid */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Casos Totales"
            value={metrics?.totalCases || 0}
            change={metrics?.weekTrend}
            icon={<Assessment sx={{ color: theme.palette.primary.main }} />}
            color={theme.palette.primary.main}
            subtitle="Esta semana"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Casos Críticos"
            value={metrics?.criticalCases || 0}
            icon={<Error sx={{ color: theme.palette.error.main }} />}
            color={theme.palette.error.main}
            subtitle="Requieren atención inmediata"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Monto en Riesgo"
            value={`$${(metrics?.totalAmount || 0).toLocaleString()}`}
            change={metrics?.monthTrend}
            icon={<AccountBalance sx={{ color: theme.palette.warning.main }} />}
            color={theme.palette.warning.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Tasa de Detección"
            value={`${metrics?.detectionRate || 0}%`}
            icon={<Speed sx={{ color: theme.palette.success.main }} />}
            color={theme.palette.success.main}
            subtitle="Precisión del sistema"
          />
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tendencia de Detección
              </Typography>
              <Box height={300}>
                {chartLoading ? (
                  <Skeleton variant="rectangular" height={300} />
                ) : (
                  <Line
                    data={trendChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        },
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          grid: {
                            color: alpha(theme.palette.divider, 0.1),
                          },
                        },
                        x: {
                          grid: {
                            display: false,
                          },
                        },
                      },
                    }}
                  />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Distribución por Severidad
              </Typography>
              <Box height={300} display="flex" alignItems="center" justifyContent="center">
                {chartLoading ? (
                  <Skeleton variant="circular" width={250} height={250} />
                ) : (
                  <Doughnut
                    data={severityDistributionData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        },
                      },
                    }}
                  />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Cases and Live Feed */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <RecentFraudCases />
        </Grid>
        <Grid item xs={12} md={5}>
          <LiveActivityFeed />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;