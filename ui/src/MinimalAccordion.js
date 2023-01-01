import * as React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { statusToColor } from './mappings'

export default function BsddAccordion({ summary, content, status }) {

  return (
    <div>
      <Accordion style={{ "width": "850px", "backgroundColor": statusToColor[status] }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel1a-content"
          id="panel1a-header"
        >
          <Typography>{summary}</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography>
            <pre>{content}</pre>
          </Typography>
        </AccordionDetails>
      </Accordion>
    </div>
  );
}




