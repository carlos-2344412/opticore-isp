import { useEffect, useState } from "react";
import "./App.css";
import Clientes from "./pages/Clientes";
import Planes from "./pages/Planes";
import Servicios from "./pages/Servicios";
import Pagos from "./pages/Pagos";
import Facturacion from "./pages/Facturacion";
import Tecnicos from "./pages/Tecnicos";
import PaginaPublica from "./PaginaPublica";

const API_URL = "http://127.0.0.1:8001";

function App() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const [logueado, setLogueado] = useState(
    !!localStorage.getItem("access_token")
  );

  const [usuarioActual, setUsuarioActual] = useState(null);

  const [pagina, setPagina] = useState("dashboard");

  const [estadisticas, setEstadisticas] = useState({
    clientes: 0,
    planes: 0,
    servicios: 0,
  });

  // ==========================================
  // PÁGINA PÚBLICA
  // ==========================================

  const esPaginaPublica =
    window.location.pathname === "/publico";

  if (esPaginaPublica) {
    return <PaginaPublica />;
  }

  // ==========================================
  // INICIAR SESIÓN
  // ==========================================

  const iniciarSesion = async (e) => {
    e.preventDefault();

    setError("");
    setCargando(true);

    try {
      const datos = new URLSearchParams();

      datos.append("username", correo);
      datos.append("password", password);

      const respuesta = await fetch(
        `${API_URL}/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body: datos,
        }
      );

      const resultado = await respuesta.json();

      if (!respuesta.ok) {
        throw new Error(
          resultado.detail ||
            "Error al iniciar sesión"
        );
      }

      localStorage.setItem(
        "access_token",
        resultado.access_token
      );

      const token = resultado.access_token;

      const respuestaUsuario = await fetch(
        `${API_URL}/auth/me`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      if (!respuestaUsuario.ok) {
        throw new Error(
          "No se pudo obtener la información del usuario"
        );
      }

      const usuario = await respuestaUsuario.json();

      setUsuarioActual(usuario);
      setLogueado(true);

      if (
        usuario.rol_id ===
        "e8b67fd6-6f1a-4d3e-a013-8599170cf7c5"
      ) {
        setPagina("tecnicos");
      } else {
        setPagina("dashboard");
      }

    } catch (error) {
      setError(error.message);

    } finally {
      setCargando(false);
    }
  };

  // ==========================================
  // CERRAR SESIÓN
  // ==========================================

  const cerrarSesion = () => {
    localStorage.removeItem("access_token");

    setLogueado(false);
    setPagina("dashboard");
    setCorreo("");
    setPassword("");
  };

  // ==========================================
  // CARGAR ESTADÍSTICAS
  // ==========================================

  useEffect(() => {
    if (!logueado) {
      return;
    }

    const cargarEstadisticas = async () => {
      try {
        const token =
          localStorage.getItem("access_token");

        const headers = {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        };

        const [
          clientesRes,
          planesRes,
          serviciosRes,
        ] = await Promise.all([
          fetch(
            `${API_URL}/clientes`,
            { headers }
          ),

          fetch(
            `${API_URL}/planes`,
            { headers }
          ),

          fetch(
            `${API_URL}/servicios`,
            { headers }
          ),
        ]);

        if (
          !clientesRes.ok ||
          !planesRes.ok ||
          !serviciosRes.ok
        ) {
          throw new Error(
            "No se pudieron cargar las estadísticas"
          );
        }

        const clientes =
          await clientesRes.json();

        const planes =
          await planesRes.json();

        const servicios =
          await serviciosRes.json();

        const serviciosActivos =
          servicios.filter(
            (servicio) =>
              servicio.estado === "activo" &&
              servicio.suspendido === false
          );

        setEstadisticas({
          clientes: clientes.length,
          planes: planes.length,
          servicios:
            serviciosActivos.length,
        });

      } catch (error) {
        console.error(
          "Error cargando estadísticas:",
          error
        );
      }
    };

    cargarEstadisticas();

  }, [logueado]);

  // ==========================================
  // LOGIN
  // ==========================================

  if (!logueado) {
    return (
      <div className="login-container">

        <div className="login-card">

          <div className="company-logo">
            <img
              src="/optirapido.jpg"
              alt="OPTIRÁPIDO"
            />
          </div>

          <p className="system-name">
            Sistema de gestión ISP
          </p>

          <form onSubmit={iniciarSesion}>

            <div className="form-group">

              <label>
                Correo electrónico
              </label>

              <input
                type="email"
                placeholder="admin@optirapido.com"
                value={correo}
                onChange={(e) =>
                  setCorreo(e.target.value)
                }
                required
              />

            </div>

            <div className="form-group">

              <label>
                Contraseña
              </label>

              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                required
              />

            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={cargando}
            >
              {cargando
                ? "Iniciando sesión..."
                : "Iniciar sesión"}
            </button>

          </form>

          <div className="login-footer">
            OPTIRÁPIDO · OptiCore
          </div>

        </div>

      </div>
    );
  }

  // ==========================================
  // PANEL PRINCIPAL
  // ==========================================

  return (
    <div className="dashboard">

      <aside className="sidebar">

        <div className="sidebar-logo">
          <img
            src="/optirapido.jpg"
            alt="OPTIRÁPIDO"
          />
        </div>

        <div className="menu">

          <div
            className={`menu-item ${
              pagina === "dashboard"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("dashboard")
            }
          >
            🏠 Dashboard
          </div>

          <div
            className={`menu-item ${
              pagina === "clientes"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("clientes")
            }
          >
            👥 Clientes
          </div>

          <div
            className={`menu-item ${
              pagina === "planes"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("planes")
            }
          >
            📦 Plan
          </div>

          <div
            className={`menu-item ${
              pagina === "servicios"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("servicios")
            }
          >
            📡 Servicios
          </div>

          <div
            className={`menu-item ${
              pagina === "pagos"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("pagos")
            }
          >
            💰 Pagos
          </div>

          <div
            className={`menu-item ${
              pagina === "facturacion"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("facturacion")
            }
          >
            🧾 Facturación
          </div>

          <div className="menu-item">
            📡 MikroTik
          </div>

          <div
            className={`menu-item ${
              pagina === "tecnicos"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setPagina("tecnicos")
            }
          >
            👨‍🔧 Técnicos
          </div>

          <div className="menu-item">
            ⚙️ Configuración
          </div>

        </div>

        <button
          className="logout-button"
          onClick={cerrarSesion}
        >
          Cerrar sesión
        </button>

      </aside>

      <main className="dashboard-main">

        {pagina === "dashboard" && (
          <>
            <header className="dashboard-header">

              <div>

                <h1>Dashboard</h1>

                <p>
                  Bienvenido al sistema de
                  gestión de OPTIRÁPIDO
                </p>

              </div>

              <div className="user-info">

                <strong>
                  Administrador
                </strong>

                <span>
                  {correo ||
                    "admin@optirapido.com"}
                </span>

              </div>

            </header>

            <section className="cards">

              <div className="stat-card">

                <span>👥</span>

                <div>

                  <p>Clientes</p>

                  <h2>
                    {estadisticas.clientes}
                  </h2>

                </div>

              </div>

              <div className="stat-card">

                <span>📡</span>

                <div>

                  <p>
                    Servicios activos
                  </p>

                  <h2>
                    {estadisticas.servicios}
                  </h2>

                </div>

              </div>

              <div className="stat-card">

                <span>📦</span>

                <div>

                  <p>Planes</p>

                  <h2>
                    {estadisticas.planes}
                  </h2>

                </div>

              </div>

              <div className="stat-card">

                <span>💰</span>

                <div>

                  <p>
                    Pagos pendientes
                  </p>

                  <h2>0</h2>

                </div>

              </div>

            </section>

            <section className="welcome-card">

              <h2>
                OPTIRÁPIDO
              </h2>

              <p>
                Sistema de gestión ISP
                listo para administrar
                clientes, planes y
                servicios.
              </p>

            </section>

          </>
        )}

        {pagina === "clientes" && (
          <Clientes />
        )}

        {pagina === "planes" && (
          <Planes />
        )}

        {pagina === "pagos" && (
          <Pagos />
        )}

        {pagina === "servicios" && (
          <Servicios />
        )}

        {pagina === "facturacion" && (
          <Facturacion />
        )}

        {pagina === "tecnicos" && (
          <Tecnicos />
        )}

      </main>

    </div>
  );
}

export default App;