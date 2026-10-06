function PaginaPublica() {
  return (
    <div
      style={{
        minHeight: "100vh",
        fontFamily: "Arial, sans-serif",
        background: "#f5f7fa",
        color: "#1f2937",
      }}
    >
      <header
        style={{
          background: "#0b5cff",
          color: "white",
          padding: "50px 20px",
          textAlign: "center",
        }}
      >
        <h1 style={{ fontSize: "42px", marginBottom: "10px" }}>
          OPTIRÁPIDO
        </h1>

        <p style={{ fontSize: "22px" }}>
          Internet por fibra óptica
        </p>

        <p>
          Magangué, Bolívar
        </p>
      </header>

      <main
        style={{
          maxWidth: "900px",
          margin: "40px auto",
          padding: "0 20px",
        }}
      >
        <section
          style={{
            background: "white",
            padding: "30px",
            borderRadius: "12px",
            marginBottom: "25px",
          }}
        >
          <h2>Internet por fibra óptica</h2>

          <p>
            Conectamos hogares y clientes con servicio de Internet
            mediante nuestra red de fibra óptica.
          </p>
        </section>

        <section
          style={{
            background: "white",
            padding: "30px",
            borderRadius: "12px",
            marginBottom: "25px",
          }}
        >
          <h2>Servicios</h2>

          <ul>
            <li>Internet residencial</li>
            <li>Internet por fibra óptica</li>
            <li>Instalaciones y soporte técnico</li>
          </ul>
        </section>

        <section
          style={{
            background: "white",
            padding: "30px",
            borderRadius: "12px",
            marginBottom: "25px",
          }}
        >
          <h2>Contacto</h2>

          <p>
            <strong>OPTIRAPIDO.NET SAS</strong>
          </p>

          <p>Magangué, Bolívar, Colombia</p>

          <p>Teléfono: 3245238853</p>

          <p>
            Correo: optirapido20@gmail.com
          </p>

          <p>
            Dirección: CL 16 A N 37 - 54 BRR SAN MATEO ICT
          </p>
        </section>
      </main>

      <footer
        style={{
          textAlign: "center",
          padding: "30px",
          background: "#111827",
          color: "white",
        }}
      >
        © 2026 OPTIRAPIDO.NET SAS
      </footer>
    </div>
  );
}

export default PaginaPublica;