import * as React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { statusToColor } from './mappings'


export default function BsddAccordion({ bsddResults, status }) {
  const bsdd = bsddResults;

  return (
    <div>
      <Accordion style={{ "width": "850px", "backgroundColor": statusToColor[status] }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel1a-content"
          id="panel1a-header"
        >
          <Typography>bSDD</Typography>
        </AccordionSummary>
        <AccordionDetails>

          <Typography>
            {

              Object.keys(bsdd["bsdd"]).map((key) => {
                return <Accordion>
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1a-content"
                    id="panel1a-header"
                  >
                    <Typography>{`Domain: ${key}`}</Typography>

                  </AccordionSummary>
                  <AccordionDetails>
                    {
                      Object.keys(bsdd["bsdd"][key]).map((classification) => {
                        return <Accordion>
                          <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                          >
                            <Typography >{`Classification: ${classification}`}</Typography>
                          </AccordionSummary>
                          <AccordionDetails>

                            {
                              Object.keys(bsdd["bsdd"][key][classification]).map((result) => {
                                return <div>
                                  {
                                    <Typography>{`   ${bsdd["bsdd"][key][classification][result]['global_id']}`}</Typography>

                                  }
                                </div>

                              }
                              )
                            }
                          </AccordionDetails>
                        </Accordion>
                      }
                      )
                    }

                  </AccordionDetails>
                </Accordion>
              })
            }
          </Typography>
        </AccordionDetails>
      </Accordion>
    </div>
  );
}