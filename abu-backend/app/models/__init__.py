# Modelos de la base de datos.

from app.models.paciente import Paciente
from app.models.responsable import Responsable
from app.models.paciente_responsable import PacienteResponsable
from app.models.perfil_corporal import PerfilCorporal
from app.models.tipo_condicion import TipoCondicion
from app.models.condicion_paciente import CondicionPaciente

from app.models.lectura_glucometro import LecturaGlucometro
from app.models.configuracion_alertas_glucosa import ConfiguracionAlertasGlucosa
from app.models.alerta import Alerta

from app.models.notificacion import Notificacion
from app.models.tratamientos_medicacion import TratamientoMedicacion
from app.models.horarios_medicacion import HorarioMedicacion
from app.models.ejecuciones_recordatorio import EjecucionRecordatorio
