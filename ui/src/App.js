import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import Disclaimer from './Disclaimer';
import Footer from './Footer'
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import SideMenu from './SideMenu';
import VerticalLinearStepper from './VerticalLinearStepper'

import { useEffect, useState } from 'react';
import { FETCH_PATH } from './environment'

import {PageContext} from './Page';
import { useContext } from 'react';
import { Typography } from '@mui/material';

function App() {

  const context = useContext(PageContext);

  const [isLoggedIn, setLogin] = useState(false);
  const [user, setUser] = useState(null)

  const [prTitle, setPrTitle] = useState("")
 
  useEffect(() => {
    fetch(context.sandboxId ? `${FETCH_PATH}/api/sandbox/me/${context.sandboxId}` : `${FETCH_PATH}/api/me`)
      .then(response => response.json())
      .then((data) => {
        if (data["redirect"] !== undefined) {
          window.location.href = data.redirect;
        }
        else {
          setLogin(true);
          setUser(data["user_data"]);
          data["sandbox_info"]["pr_title"] && setPrTitle(data["sandbox_info"]["pr_title"]);
        }
      })
  }, []);

  document.body.style.overflow = "hidden";
  if (isLoggedIn) {
    return (
      <div class="home">
        <Grid direction="column"
          container
          style={{
            minHeight: '100vh', alignItems: 'stretch',
          }} >
          <ResponsiveAppBar user={user} />
          <Grid
            container
            flex={1}
            direction="row"
            style={{
            }}
          >
            <SideMenu />
            
            <Grid
              container
              flex={1}
              direction="column"
              style={{
                justifyContent: "space-between",
                overflow: 'scroll',
                boxSizing: 'border-box',
                maxHeight: '90vh',
                overflowX: 'hidden'
              }}
            >
              <div style={{
                gap: '10px',
                flex: 1
              }}>
                <Grid
                  container
                  spacing={0}
                  direction="column"
                  alignItems="center"
                  justifyContent="space-between"
                  style={{
                    minHeight: '100vh',
                    background: `url(${require('./background.jpg')}) fixed`,
                    backgroundSize: 'cover',
                    border: context.sandboxId ? 'solid 12px red' : 'none',
                    gap: '12em'
                  }}
                >
                  {context.sandboxId && <h2
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

                  <Box sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    alignSelf: 'center',
                    borderRadius: '4px',
                    boxShadow: 'rgb(0 0 0 / 50%) 2px 2px 8px',
                    backgroundColor: '#ffffff',
                    padding: '0px 32px 0px 0px'
                  }}>
                    <Box
                      style={{
                        display: 'flex',
                        flexDirection: 'row',
                        alignItems: 'center',
                        marginLeft: '5px',
                        gap: '55px'
                      }}>
                      <Dz />
                      <VerticalLinearStepper />
                    </Box>
                  </Box>
                    
                  <div style={{alignSelf:"start", backgroundColor: '#ffffffe0', padding: '0.5em 5em', boxSizing: 'border-box', borderTop: 'thin solid rgb(238, 238, 238)', width: '100%'}}>
                    <Typography style={{fontWeight: 'bold'}} sx={{paddingTop: '2em'}}>What it is</Typography>
                    <Typography align='left' paragraph>The bSI Validation Service is a free, online platform for validating IFC files, developed by buildingSMART – with the help of software vendors and bSI projects</Typography>

                    <Typography style={{fontWeight: 'bold'}}>What it does</Typography>

                    <Typography align='left' paragraph>Given an IFC file, the Validation Service provides a judgment of conformity for such file against the IFC standard (schema and specification)</Typography>

                    <Typography style={{fontWeight: 'bold'}}>What is being checked</Typography>

                    <Typography align='left' paragraph>The IFC file is valid when it conforms to:

                    <ul>
                        <li><b>Syntax</b> The STEP Physical File syntax</li>
                        <li><b>Schema</b> The IFC schema referenced in the file including formal propositions encoded in the EXPRESS where rule and function language</li>
                        <li><b>Rules</b> Other normative rules of the IFC specification (e.g. implementer agreements and informal propositions)</li>
                        <li><b>bSDD</b> The Validation Service validates the content of an IFC file against the requirements encoded in the bSDD domain referenced from a classification encoded in the file</li>
                    </ul>

                    </Typography>

                    <Typography style={{fontWeight: 'bold'}}>What is NOT being checked</Typography>

                    <Typography align='left' paragraph>Outside of the constraints encoded in bSDD, the bSI Validation Service does not check project-specific, national-specific, organization-specific rules or constraints. Case-specific validation is where the mandate of the bSI Validation Service ends.</Typography>

                    <Typography style={{fontWeight: 'bold'}}>Visualisation</Typography>

                    <Typography align='left' paragraph sx={{paddingBottom: '2em'}}>For multiple reasons, geometric visualisation is not within the scope nor the mandate of the Validation Service. Many errors are invisible in a viewer or unrelated to a geometric representation or prevent visualisation altogether.</Typography>

                    <Footer/>
                  </div>
                
                </Grid>
              </div>
            </Grid>
          </Grid>
        </Grid>
      </div>

    );
  }
}

export default App;
