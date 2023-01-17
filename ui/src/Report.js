import ResponsiveAppBar from './ResponsiveAppBar'
import Disclaimer from './Disclaimer';
import { useParams } from 'react-router-dom'

import Footer from './Footer'
import Grid from '@mui/material/Grid';
import GeneralTable from './GeneralTable';
import MinimalTreeView from './MinimalTreeView.js'
import BsddTreeView from './BsddTreeView'
import GherkinResults from './GherkinResult';

import { useEffect, useState } from 'react';
import { FETCH_PATH } from './environment'

function Report() {
  const [isLoggedIn, setLogin] = useState(false);
  const [reportData, setReportData] = useState({});
  const [user, setUser] = useState(null)
  const [isLoaded, setLoadingStatus] = useState(false)

  const { modelCode } = useParams()

  useEffect(() => {
    fetch(`${FETCH_PATH}/api/me`)
      .then(response => response.json())
      .then((data) => {
        if (data["redirect"] !== undefined) {
          window.location.href = data.redirect;
        }
        else {
          setLogin(true);
          setUser(data["user_data"]);
        }
      })
  }, []);

  function getReport(code) {
    fetch(`${FETCH_PATH}/api/report2/${code}`)
      .then(response => response.json())
      .then((data) => {
        setReportData(data);
        setLoadingStatus(true);
      })
  }

  useEffect(() => {
    getReport(modelCode);
  }, []);

  if (isLoggedIn && isLoaded) {
    console.log("Report data ", reportData)
    return (
      <div>
        <Grid
          container
          spacing={0}
          direction="column"
          alignItems="center"
          justifyContent="space-between"
          style={{ minHeight: '100vh', gap: '15px', backgroundColor: 'rgb(238, 238, 238)' }}
        >
          <ResponsiveAppBar user={user} />
          <Disclaimer />

          <GeneralTable data={reportData} type={"general"} />
          <GeneralTable data={reportData} type={"overview"} />

          <MinimalTreeView status={reportData["model"]["status_syntax"]} summary={"Syntax"} content={reportData["results"]["syntax_result"]["msg"]} />
          <MinimalTreeView status={reportData["model"]["status_schema"]} summary={"Schema"} content={reportData["results"]["schema_result"]["msg"]} />

          <BsddTreeView status={reportData["model"]["status_bsdd"]} summary={"bSDD"} bsddResults={reportData["results"]["bsdd_results"]} />

          <GherkinResults status={reportData["model"]["status_ia"]} gherkin_task={reportData.tasks["implementer_agreements_task"]} task_type="implementer_agreements_task" />
          <GherkinResults status={reportData["model"]["status_ip"]} gherkin_task={reportData.tasks["informal_propositions_task"]} task_type="informal_propositions_task" />
          <Footer />
        </Grid>
      </div>
    );
  }
}

export default Report;
