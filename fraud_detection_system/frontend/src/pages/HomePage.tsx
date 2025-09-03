/**
 * Página de inicio del sistema
 * frontend/src/pages/HomePage.tsx
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Paper,
  Stack,
  Divider,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  Speed as SpeedIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Detección en Tiempo Real',
      description: 'Monitoreo continuo de transacciones con alertas instantáneas',
      icon: <SpeedIcon fontSize="large" color="primary" />,
    },
    {
      title: 'Análisis Basado en Reglas',
      description: 'Sistema de detección sin ML, 100% explicable y auditable',
      icon: <AssessmentIcon fontSize="large" color="primary" />,
    },
    {
      title: 'Multi-Detector',
      description: 'Tres detectores especializados para diferentes tipos de fraude',
      icon: <WarningIcon fontSize="large" color="primary" />,
    },
    {
      title: 'Dashboard Interactivo',
      description: 'Visualización completa con gráficos y estadísticas en tiempo real',
      icon: <DashboardIcon fontSize="large" color="primary" />,
    },
    {
      title: 'Alta Seguridad',
      description: 'Auditoría completa y trazabilidad de todas las operaciones',
      icon: <ShieldIcon fontSize="large" color="primary" />,
    },
    {
      title: 'Gestión de Casos',
      description: 'Flujo completo desde detección hasta resolución',
      icon: <SecurityIcon fontSize="large" color="primary" />,
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ py: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon sx={{ color: 'white', fontSize: 32 }} />
              <Typography variant="h5" sx={{ color: 'white', fontWeight: 600 }}>
                Sistema de Detección de Fraude
              </Typography>
            </Box>
            <Button
              variant="contained"
              onClick={() => navigate('/dashboard')}
              sx={{
                backgroundColor: 'white',
                color: '#667eea',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                },
              }}
            >
              Ir al Dashboard
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Hero Section */}
      <Container maxWidth="lg" sx={{ flex: 1, display: 'flex', flexDirection: 'column', py: 6 }}>
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Typography variant="h2" sx={{ color: 'white', fontWeight: 700, mb: 2 }}>
            Proteja su Empresa del Fraude
          </Typography>
          <Typography variant="h5" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 4 }}>
            Detección inteligente basada en reglas de negocio explícitas
          </Typography>
          <Stack direction="row" spacing={2} justifyContent="center">
            <Button
              variant="contained"
              size="large"
              startIcon={<DashboardIcon />}
              onClick={() => navigate('/dashboard')}
              sx={{
                backgroundColor: 'white',
                color: '#667eea',
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                },
              }}
            >
              Acceder al Sistema
            </Button>
          </Stack>
        </Box>

        {/* Stats */}
        <Paper
          elevation={0}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderRadius: 3,
            p: 3,
            mb: 6,
          }}
        >
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="primary" fontWeight="bold">
                  3
                </Typography>
                <Typography variant="body1" color="textSecondary">
                  Detectores Activos
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="primary" fontWeight="bold">
                  24/7
                </Typography>
                <Typography variant="body1" color="textSecondary">
                  Monitoreo Continuo
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="primary" fontWeight="bold">
                  100%
                </Typography>
                <Typography variant="body1" color="textSecondary">
                  Explicable
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="primary" fontWeight="bold">
                  &lt;1s
                </Typography>
                <Typography variant="body1" color="textSecondary">
                  Tiempo Detección
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Features */}
        <Typography variant="h4" sx={{ color: 'white', fontWeight: 600, mb: 4, textAlign: 'center' }}>
          Características del Sistema
        </Typography>
        <Grid container spacing={3}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-5px)',
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" component="h3" gutterBottom align="center">
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" align="center">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Detectores Info */}
        <Box sx={{ mt: 6 }}>
          <Typography variant="h4" sx={{ color: 'white', fontWeight: 600, mb: 4, textAlign: 'center' }}>
            Detectores Especializados
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  Anomalías en Facturas
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Stack spacing={1} sx={{ mt: 2 }}>
                  <Typography variant="body2">• Montos redondos repetitivos</Typography>
                  <Typography variant="body2">• Secuencias faltantes</Typography>
                  <Typography variant="body2">• Facturas fuera de horario</Typography>
                  <Typography variant="body2">• Descuentos excesivos</Typography>
                </Stack>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  Robo de Combustible
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Stack spacing={1} sx={{ mt: 2 }}>
                  <Typography variant="body2">• Consumo anormal</Typography>
                  <Typography variant="body2">• Repostajes excesivos</Typography>
                  <Typography variant="body2">• Diferencias en tanques</Typography>
                  <Typography variant="body2">• Patrones sospechosos</Typography>
                </Stack>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3, backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  Manipulación de Datos
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Stack spacing={1} sx={{ mt: 2 }}>
                  <Typography variant="body2">• Cambios masivos</Typography>
                  <Typography variant="body2">• Eliminaciones sospechosas</Typography>
                  <Typography variant="body2">• Modificaciones fuera de horario</Typography>
                  <Typography variant="body2">• Alteraciones no autorizadas</Typography>
                </Stack>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* CTA Final */}
        <Box sx={{ mt: 6, textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<SecurityIcon />}
            onClick={() => navigate('/dashboard')}
            sx={{
              backgroundColor: 'white',
              color: '#667eea',
              px: 5,
              py: 2,
              fontSize: '1.2rem',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
              },
            }}
          >
            Comenzar Detección
          </Button>
        </Box>
      </Container>

      {/* Footer */}
      <Box
        sx={{
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          borderTop: '1px solid rgba(255, 255, 255, 0.2)',
          py: 3,
          mt: 'auto',
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="white" align="center">
            © 2025 Sistema de Detección de Fraude - v1.0.0
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default HomePage;