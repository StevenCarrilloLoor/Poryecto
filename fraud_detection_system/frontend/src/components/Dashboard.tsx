/**
 * Componente Dashboard principal
 * frontend/src/components/Dashboard.tsx
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  IconButton,
  Alert,
  Snackbar,
  TextField,
  MenuItem,
  AppBar,
  Toolbar,
  Badge,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridRenderCellParams,
  GridToolbar,
} from '@mui/x-data-grid';
import {
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  Notifications as NotificationsIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
  LocalGasStation as GasIcon,
  Receipt as ReceiptIcon,
  DataUsage as DataIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

import { apiService, FraudCase, DashboardStats, FraudStatus } from '../services/api';

// Colores para gráficos
const COLORS = {
  CRITICO: '#d32f2f',
  ALTO: '#f57c00',
  MEDIO: '#fbc02d',
  BAJO: '#388e3c',
};

const Dashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCase, setSelectedCase] = useState<FraudCase | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [newStatus, setNewStatus] = useState<FraudStatus | ''>('');
  const [statusNotes, setStatusNotes] = useState('');
  const [notifications, setNotifications] = useState<string[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Query para obtener estadísticas del dashboard
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: apiService.getDashboardStats,
    refetchInterval: 30000, // Auto-refresh cada 30 segundos
  });

  // Query para obtener casos de fraude
  const { data: fraudCases = [], isLoading: casesLoading, refetch: refetchCases } = useQuery<FraudCase[]>({
    queryKey: ['fraudCases'],
    queryFn: () => apiService.getFraudCases(),
    refetchInterval: 30000,
  });

  // Mutation para actualizar estado de caso
  const updateStatusMutation = useMutation({
    mutationFn: ({ caseId, status, notes }: { caseId: number; status: FraudStatus; notes: string }) =>
      apiService.updateCaseStatus(caseId, status, notes, 'Usuario'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fraudCases'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setSnackbarMessage('Estado actualizado correctamente');
      setSnackbarOpen(true);
      setStatusDialogOpen(false);
      setNewStatus('');
      setStatusNotes('');
    },
    onError: () => {
      setSnackbarMessage('Error al actualizar el estado');
      setSnackbarOpen(true);
    },
  });

  // Mutation para ejecutar detección manual
  const runDetectionMutation = useMutation({
    mutationFn: apiService.runDetection,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['fraudCases'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setSnackbarMessage(`Detección completada: ${data.cases_detected} casos encontrados`);
      setSnackbarOpen(true);
    },
    onError: () => {
      setSnackbarMessage('Error al ejecutar detección');
      setSnackbarOpen(true);
    },
  });

  // Conectar WebSocket para notificaciones en tiempo real
  useEffect(() => {
    const ws = apiService.connectWebSocket((data) => {
      if (data.event === 'new_case' || data.event === 'auto_detection') {
        const newNotification = `Nuevo caso detectado: ${data.case.title}`;
        setNotifications(prev => [newNotification, ...prev].slice(0, 10));
        queryClient.invalidateQueries({ queryKey: ['fraudCases'] });
        queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      }
    });

    return () => {
      ws.close();
    };
  }, [queryClient]);

  // Columnas para el DataGrid
  const columns: GridColDef[] = [
    {
      field: 'case_number',
      headerName: 'Número de Caso',
      width: 150,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'title',
      headerName: 'Título',
      width: 300,
      flex: 1,
    },
    {
      field: 'detector_type',
      headerName: 'Tipo',
      width: 150,
      renderCell: (params) => {
        const icons: { [key: string]: JSX.Element } = {
          ANOMALIA_FACTURA: <ReceiptIcon fontSize="small" />,
          ROBO_COMBUSTIBLE: <GasIcon fontSize="small" />,
          MANIPULACION_DATOS: <DataIcon fontSize="small" />,
        };
        return (
          <Box display="flex" alignItems="center" gap={0.5}>
            {icons[params.value] || <WarningIcon fontSize="small" />}
            <Typography variant="body2">{params.value}</Typography>
          </Box>
        );
      },
    },
    {
      field: 'severity',
      headerName: 'Severidad',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          sx={{
            backgroundColor: COLORS[params.value as keyof typeof COLORS],
            color: 'white',
          }}
        />
      ),
    },
    {
      field: 'status',
      headerName: 'Estado',
      width: 130,
      renderCell: (params) => {
        const statusColors: { [key: string]: 'default' | 'warning' | 'success' | 'error' | 'info' } = {
          PENDIENTE: 'warning',
          CONFIRMADO: 'error',
          RECHAZADO: 'default',
          INVESTIGANDO: 'info',
          RESUELTO: 'success',
        };
        return (
          <Chip
            label={params.value}
            size="small"
            color={statusColors[params.value] || 'default'}
          />
        );
      },
    },
    {
      field: 'amount',
      headerName: 'Monto',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2">
          ${params.value ? params.value.toLocaleString('es-ES', { minimumFractionDigits: 2 }) : '0.00'}
        </Typography>
      ),
    },
    {
      field: 'detection_date',
      headerName: 'Fecha Detección',
      width: 150,
      renderCell: (params) => (
        <Typography variant="body2">
          {format(new Date(params.value), 'dd/MM/yyyy HH:mm', { locale: es })}
        </Typography>
      ),
    },
    {
      field: 'confidence_score',
      headerName: 'Confianza',
      width: 100,
      renderCell: (params) => (
        <Box sx={{ width: '100%' }}>
          <Typography variant="caption">{params.value || 0}%</Typography>
          <LinearProgress
            variant="determinate"
            value={params.value || 0}
            sx={{
              height: 4,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: params.value > 75 ? '#4caf50' : params.value > 50 ? '#ff9800' : '#f44336',
              },
            }}
          />
        </Box>
      ),
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 100,
      sortable: false,
      renderCell: (params) => (
        <Button
          size="small"
          variant="outlined"
          onClick={() => {
            setSelectedCase(params.row as FraudCase);
            setDetailsOpen(true);
          }}
        >
          Ver
        </Button>
      ),
    },
  ];

  // Preparar datos para gráficos
  const severityChartData = stats
    ? Object.entries(stats.cases_by_severity).map(([key, value]) => ({
        name: key,
        value: value,
      }))
    : [];

  const statusChartData = stats
    ? [
        { name: 'Pendientes', value: stats.pending_cases, color: '#ff9800' },
        { name: 'Confirmados', value: stats.confirmed_cases, color: '#f44336' },
        { name: 'Rechazados', value: stats.rejected_cases, color: '#9e9e9e' },
      ]
    : [];

  return (
    <Box sx={{ flexGrow: 1, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar position="static">
        <Toolbar>
          <SecurityIcon sx={{ mr: 2 }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Sistema de Detección de Fraude
          </Typography>
          <Tooltip title="Ejecutar Detección Manual">
            <IconButton
              color="inherit"
              onClick={() => runDetectionMutation.mutate()}
              disabled={runDetectionMutation.isPending}
            >
              <PlayArrowIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Actualizar">
            <IconButton
              color="inherit"
              onClick={() => {
                refetchStats();
                refetchCases();
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Badge badgeContent={notifications.length} color="error">
            <IconButton color="inherit">
              <NotificationsIcon />
            </IconButton>
          </Badge>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
        <Grid container spacing={3}>
          {/* Estadísticas */}
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Casos
                </Typography>
                <Typography variant="h4">
                  {stats?.total_cases || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Casos Pendientes
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {stats?.pending_cases || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Monto Total
                </Typography>
                <Typography variant="h4">
                  ${stats?.total_amount?.toLocaleString('es-ES', { minimumFractionDigits: 2 }) || '0.00'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Detectados Hoy
                </Typography>
                <Typography variant="h4" color="primary">
                  {stats?.detection_rate_today || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Gráficos */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: 300 }}>
              <Typography variant="h6" gutterBottom>
                Casos por Severidad
              </Typography>
              <ResponsiveContainer width="100%" height="90%">
                <PieChart>
                  <Pie
                    data={severityChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: 300 }}>
              <Typography variant="h6" gutterBottom>
                Estado de Casos
              </Typography>
              <ResponsiveContainer width="100%" height="90%">
                <BarChart data={statusChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="value" fill="#8884d8">
                    {statusChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Tabla de Casos */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, height: 600 }}>
              <Typography variant="h6" gutterBottom>
                Casos de Fraude Detectados
              </Typography>
              <DataGrid
                rows={fraudCases}
                columns={columns}
                loading={casesLoading}
                pageSizeOptions={[10, 25, 50, 100]}
                initialState={{
                  pagination: {
                    paginationModel: { pageSize: 25, page: 0 },
                  },
                  sorting: {
                    sortModel: [{ field: 'detection_date', sort: 'desc' }],
                  },
                }}
                slots={{
                  toolbar: GridToolbar,
                }}
                sx={{
                  '& .MuiDataGrid-cell:hover': {
                    color: 'primary.main',
                  },
                }}
              />
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Dialog de Detalles del Caso */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Detalles del Caso: {selectedCase?.case_number}
        </DialogTitle>
        <DialogContent dividers>
          {selectedCase && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="h6">{selectedCase.title}</Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  {selectedCase.description}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Estado:</Typography>
                <Chip label={selectedCase.status} color="primary" />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Severidad:</Typography>
                <Chip 
                  label={selectedCase.severity}
                  sx={{
                    backgroundColor: COLORS[selectedCase.severity as keyof typeof COLORS],
                    color: 'white',
                  }}
                />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Monto:</Typography>
                <Typography variant="body1">
                  ${selectedCase.amount?.toLocaleString('es-ES', { minimumFractionDigits: 2 }) || '0.00'}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Confianza:</Typography>
                <Typography variant="body1">{selectedCase.confidence_score || 0}%</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Cliente:</Typography>
                <Typography variant="body1">{selectedCase.client_name || 'N/A'}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">RUC:</Typography>
                <Typography variant="body1">{selectedCase.client_ruc || 'N/A'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2">Fecha de Detección:</Typography>
                <Typography variant="body1">
                  {format(new Date(selectedCase.detection_date), 'dd/MM/yyyy HH:mm:ss', { locale: es })}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Cerrar</Button>
          <Button
            variant="contained"
            onClick={() => {
              setStatusDialogOpen(true);
            }}
          >
            Actualizar Estado
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de Actualización de Estado */}
      <Dialog open={statusDialogOpen} onClose={() => setStatusDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Actualizar Estado del Caso</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                select
                fullWidth
                label="Nuevo Estado"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as FraudStatus)}
              >
                <MenuItem value="PENDIENTE">Pendiente</MenuItem>
                <MenuItem value="CONFIRMADO">Confirmado</MenuItem>
                <MenuItem value="RECHAZADO">Rechazado</MenuItem>
                <MenuItem value="INVESTIGANDO">Investigando</MenuItem>
                <MenuItem value="RESUELTO">Resuelto</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Notas"
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
                placeholder="Ingrese notas o comentarios sobre esta actualización..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (selectedCase && newStatus) {
                updateStatusMutation.mutate({
                  caseId: selectedCase.id,
                  status: newStatus as FraudStatus,
                  notes: statusNotes,
                });
              }
            }}
            disabled={!newStatus || updateStatusMutation.isPending}
          >
            Actualizar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar para notificaciones */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default Dashboard;