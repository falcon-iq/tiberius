


export default async function Index() {
  const res = await fetch(
    "http://localhost:8080/api/generic-bean-api/metadata/OKR_STATUS"
  );
  const data = await res.json();

  return (
    <div className="wrapper">
      <div className="container">
        <div id="welcome">
          <h1>
            <span> Hello there, </span>
            Welcome @tiberius/falcon-iq-web-app 👋
          </h1>
          <div>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        </div>
      </div>
    </div>
  );
};
