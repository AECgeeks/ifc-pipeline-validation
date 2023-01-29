import * as React from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';
import { statusToColor } from './mappings'

export default function MinimalTreeView({ summary, content, status }) {
  return (
    <TreeView
      aria-label="file system navigator"
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
      defaultExpanded={["0"]}
      sx={{"width":"100%", "max-width": "850px", "backgroundColor": statusToColor[status], "overflow-x": "auto"}}
    >
      <TreeItem nodeId="0" label={summary}>
        <pre>{content}</pre>
      </TreeItem>
    </TreeView>
  );
}