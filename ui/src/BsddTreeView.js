import * as React from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';
import { statusToColor } from './mappings'
import Typography from '@mui/material/Typography';


export default function BsddTreeView({ bsddResults, status }) {

  const bsdd = bsddResults;

  return (
    <TreeView
      aria-label="file system navigator"
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
      defaultExpanded={["0"]}
      sx={{ "width": "850px", "backgroundColor": statusToColor[status] }}
    >
      <TreeItem nodeId="0" label={"bSDD"}>
        <TreeView defaultCollapseIcon={<ExpandMoreIcon />}
          defaultExpandIcon={<ChevronRightIcon />}>
          {
            Object.keys(bsdd["bsdd"]).map((domain, d_index) => {
              return <TreeItem nodeId={d_index} label={`Domain: ${domain}`}>
                <TreeView defaultCollapseIcon={<ExpandMoreIcon />}
                  defaultExpandIcon={<ChevronRightIcon />}>
                  {
                    Object.keys(bsdd["bsdd"][domain]).map((classification, c_index) => {
                      return <TreeItem nodeId={c_index} label={`Classification: ${classification}`}>
                        {
                          Object.keys(bsdd["bsdd"][domain][classification]).map((result) => {
                            return <div>
                              <Typography>{`${bsdd["bsdd"][domain][classification][result]['global_id']}`}</Typography>
                            </div>
                          }
                          )
                        }
                      </TreeItem>
                    }
                    )
                  }
                </TreeView>
              </TreeItem>
            })
          }
        </TreeView>
      </TreeItem>
    </TreeView>
  );
}