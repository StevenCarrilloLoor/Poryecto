/**
 * Servicio API para comunicación con el backend
 * frontend/src/services/api.ts
 */

import axios, { AxiosInstance } from 'axios';

// Configuración de la API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// Tipos de datos
export enum FraudStatus {
  PENDING = 'PENDIENTE',
  CONFIRMED = 'CONFIRMADO',
  REJECTED = 'RECHAZADO',
  INVESTIGATING = 'INVESTIGANDO',
  RESOLVED = 'RESUELTO',
}

export enum FraudSeverity {
  LOW = 'BAJO',
  MEDIUM = 'MEDIO',
  HIGH = 'ALTO',
  CRITICAL = 'CRITICO',
}

export enum DetectorType {
  INVOICE_ANOMALY = 'ANOMALIA_FACTURA',
  FUEL_THEFT = 'ROBO_COMBUSTIBLE',
  DATA_MANIPULATION = 'MANIPULACION_DATOS',
  DUPLICATE_TRANSACTION = 'TRANSACCION_DUPLICADA',
  EXCESSIVE_DISCOUNT = 'DESCUENTO_EXCESIVO',
  AFTERHOURS = 'FUERA_HORARIO',
  ROUND_AMOUNT = 'MONTO_REDONDO',
  SEQUENCE_GAP = 'SECUENCIA_FALTANTE',
}

export interface FraudCase {
  id: number;
  case_number: string;
  detector_type: string;
  severity: string;
  status: string;
  title: string;
  description?: string;
  amount?: number;
  client_code?: string;
  client_name?: string;
  client_ruc?: string;
  detection_date: string;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardStats {
  total_cases: number;
  pending_cases: number;
  confirmed_cases: number;
  rejected_cases: number;
  total_amount: number;
  cases_by_severity: { [key: string]: number };
  recent_cases: FraudCase[];
  detection_rate_today: number;
  detection_rate_week: number;
}

export interface DetectorConfig {
  id: number;
  detector_type: string;
  enabled: boolean;
  name: string;
  description?: string;
  last_run?: string;
  config: any;
}

export interface RunDetectionRequest {
  detector_types?: DetectorType[];
  date_from?: string;
  date_to?: string;
}

export interface RunDetectionResponse {
  success: boolean;
  cases_detected: number;
  results: Array<{
    detector: string;
    case_id: number;
    case_number: string;
    title: string;
  }>;
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para manejo de errores
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        if (error.response?.status === 401) {
          // Manejar autenticación si es necesario
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Casos de Fraude
  async getFraudCases(params?: {
    status?: FraudStatus;
    detector_type?: DetectorType;
    date_from?: string;
    date_to?: string;
    limit?: number;
  }): Promise<FraudCase[]> {
    const response = await this.api.get<FraudCase[]>('/fraud-cases', { params });
    return response.data;
  }

  async getFraudCase(caseId: number): Promise<FraudCase> {
    const response = await this.api.get<FraudCase>(`/fraud-cases/${caseId}`);
    return response.data;
  }

  async updateCaseStatus(
    caseId: number,
    status: FraudStatus,
    notes: string,
    user: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await this.api.patch(`/fraud-cases/${caseId}/status`, {
      status,
      notes,
      user,
    });
    return response.data;
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.api.get<DashboardStats>('/dashboard/stats');
    return response.data;
  }

  // Detección
  async runDetection(request?: RunDetectionRequest): Promise<RunDetectionResponse> {
    const response = await this.api.post<RunDetectionResponse>('/run-detection', request || {});
    return response.data;
  }

  // Configuración
  async getDetectorConfigs(): Promise<DetectorConfig[]> {
    const response = await this.api.get<DetectorConfig[]>('/detector-configs');
    return response.data;
  }

  async updateDetectorConfig(
    configId: number,
    updates: Partial<DetectorConfig>
  ): Promise<{ success: boolean }> {
    const response = await this.api.patch(`/detector-configs/${configId}`, updates);
    return response.data;
  }

  // WebSocket para notificaciones en tiempo real
  connectWebSocket(onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(WS_BASE_URL);

    ws.onopen = () => {
      console.log('WebSocket conectado');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket desconectado');
      // Intentar reconectar después de 5 segundos
      setTimeout(() => {
        this.connectWebSocket(onMessage);
      }, 5000);
    };

    // Mantener conexión viva
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);

    // Limpiar al cerrar
    const originalClose = ws.close;
    ws.close = function () {
      clearInterval(pingInterval);
      originalClose.call(ws);
    };

    return ws;
  }
}

// Exportar instancia única del servicio
export const apiService = new ApiService();