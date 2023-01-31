import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import Disclaimer from './Disclaimer';
import Footer from './Footer'
import Grid from '@mui/material/Grid';
import { useEffect, useState } from 'react';
import { FETCH_PATH } from './environment'

function App() {
  const [isLoggedIn, setLogin] = useState(false);
  const [user, setUser] = useState(null)

  const splittedUrl = window.location.href.split("/");
  const [sandboxCommit, setSandbox] = useState(
      splittedUrl.includes("sandbox")?
      splittedUrl.at(-1):false);

  const [prTitle, setPrTitle] = useState("")
  const [commitId, setCommitId] = useState("")

  useEffect(() => {
    fetch(sandboxCommit?`${FETCH_PATH}/api/sandbox/me/${sandboxCommit}`:`${FETCH_PATH}/api/me`)
      .then(response => response.json())
      .then((data) => {
        if (data["redirect"] !== undefined) {
          window.location.href = data.redirect;
        }
        else {
          setLogin(true);
          setUser(data["user_data"]);
          data["sandbox_info"]["pr_title"] && setPrTitle(data["sandbox_info"]["pr_title"]);
          data["sandbox_info"]["commit_id"] && setCommitId(data["sandbox_info"]["commit_id"]);
        }
      })
  }, []);

  if (isLoggedIn) {
    return (
      <div>
        <Grid
          container
          spacing={0}
          direction="column"
          alignItems="center"
          justifyContent="space-between"
          style={{ minHeight: '100vh', gap: '15px', backgroundImage: 'url(' + require('./background.jpg') + ')', border: sandboxCommit?'solid 12px red':'none'}}
        >
          <ResponsiveAppBar user={user} />
          {sandboxCommit && <h2
          style={{
            background: "red",
            color: "white",
            marginTop: "-16px",
            lineHeight: "30px",
            padding: "12px",
            borderRadius: "0 0 16px 16px"
          }}
           >Sandbox for <b>{prTitle}</b></h2>}
          <Disclaimer />
          <Dz />
          <Footer />
        </Grid>
      </div>


    );
  }
}

export default App;
