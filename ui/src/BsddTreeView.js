import * as React from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { statusToColor } from './mappings'

export default function BsddTreeView({ bsddResults, status }) {

  const bsdd = bsddResults;

  return (
    <Paper sx={{overflow: 'hidden'}}><TreeView
      aria-label="file system navigator"
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
      defaultExpanded={["0"]}
      sx={{ "width": "850px", "backgroundColor": statusToColor[status], "> li > .MuiTreeItem-content": { padding: "16px" }, ".MuiTreeItem-content.Mui-expanded": { borderBottom: 'solid 1px black' } }}
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
                            return <div >
                              <br></br>
                              <TableContainer sx={{
                                minWidth: 650,
                                "width": "90%",
                                "padding": "10px"
                              }} >
                                <Table sx={{
                                  minWidth: 650,
                                  "backgroundColor": "rgb(238, 238, 238)",
                                }}
                                  size="small"
                                  aria-label="a dense table">
                                  <TableHead>
                                    <TableRow>
                                      <TableCell align="center">Instance</TableCell>
                                      <TableCell align="center">Requirement</TableCell>
                                      <TableCell align="center">Required</TableCell>
                                      <TableCell align="center">Observed</TableCell>

                                    </TableRow>
                                  </TableHead>
                                  <TableBody>

                                    {/* IFC TYPE */}
                                    <TableRow
                                      key={"0"}
                                      sx={{ '&:last-child td, &:last-child th': { border: 0 }, "backgroundColor": (bsdd["bsdd"][domain][classification][result]["val_ifc_type"] == 1) ? statusToColor['v'] : statusToColor['i'] }}
                                    >
                                      <TableCell align="center" component="th" scope="row">
                                        {`${bsdd["bsdd"][domain][classification][result]['global_id']}`}
                                      </TableCell>
                                      <TableCell align="center"> {"IFC entity type"}</TableCell>
                                      <TableCell align="center"> {`${bsdd["bsdd"][domain][classification][result]["bsdd_type_constraint"]}`}</TableCell>
                                      <TableCell align="center">  {`${bsdd["bsdd"][domain][classification][result]['ifc_type']}`}</TableCell>
                                    </TableRow>

                                    {/* PROPERTY SET */}
                                    <TableRow
                                      key={"1"}
                                      sx={{ '&:last-child td, &:last-child th': { border: 0 }, "backgroundColor": (bsdd["bsdd"][domain][classification][result]["val_property_set"] == 1) ? statusToColor['v'] : statusToColor['i'] }}
                                    >
                                      <TableCell align="center" component="th" scope="row">
                                        {`${bsdd["bsdd"][domain][classification][result]['global_id']}`}
                                      </TableCell>
                                      <TableCell align="center"> {"Property Set"}</TableCell>
                                      <TableCell align="center"> {`${bsdd["bsdd"][domain][classification][result]["bsdd_property_constraint"]["propertySet"]}`}</TableCell>
                                      <TableCell align="center">  {`${bsdd["bsdd"][domain][classification][result]['ifc_property_set']}`}</TableCell>
                                    </TableRow>

                                    {/* PROPERTY */}
                                    <TableRow
                                      key={"2"}
                                      sx={{ '&:last-child td, &:last-child th': { border: 0 }, "backgroundColor": (bsdd["bsdd"][domain][classification][result]["val_property_name"] == 1) ? statusToColor['v'] : statusToColor['i'] }}
                                    >
                                      <TableCell align="center" component="th" scope="row">
                                        {`${bsdd["bsdd"][domain][classification][result]['global_id']}`}
                                      </TableCell>
                                      <TableCell align="center"> {"Property Value"}</TableCell>
                                      <TableCell align="center"> {`${bsdd["bsdd"][domain][classification][result]["bsdd_property_constraint"]["name"]}`}</TableCell>
                                      <TableCell align="center">  {`${bsdd["bsdd"][domain][classification][result]['ifc_property_value']}`}</TableCell>
                                    </TableRow>

                                    {/* DATA TYPE */}
                                    <TableRow
                                      key={"3"}
                                      sx={{ '&:last-child td, &:last-child th': { border: 0 }, "backgroundColor": (bsdd["bsdd"][domain][classification][result]["val_property_type"] == 1) ? statusToColor['v'] : statusToColor['i'] }}
                                    >
                                      <TableCell align="center" component="th" scope="row">
                                        {`${bsdd["bsdd"][domain][classification][result]['global_id']}`}
                                      </TableCell>
                                      <TableCell align="center"> {"Property Value Type"}</TableCell>
                                      <TableCell align="center"> {`${bsdd["bsdd"][domain][classification][result]["bsdd_property_constraint"]["dataType"]}`}</TableCell>
                                      <TableCell align="center">  {`${bsdd["bsdd"][domain][classification][result]['ifc_property_type']}`}</TableCell>
                                    </TableRow>

                                    {/* PROPERTY VALUE */}
                                    <TableRow
                                      key={"4"}
                                      sx={{ '&:last-child td, &:last-child th': { border: 0 }, "backgroundColor": (bsdd["bsdd"][domain][classification][result]["val_property_value"] == 1) ? statusToColor['v'] : statusToColor['i'] }}
                                    >
                                      <TableCell align="center" component="th" scope="row">
                                        {`${bsdd["bsdd"][domain][classification][result]['global_id']}`}
                                      </TableCell>
                                      <TableCell align="center"> {"Property Value Type"}</TableCell>
                                      <TableCell align="center"> {`${bsdd["bsdd"][domain][classification][result]["bsdd_property_constraint"]["predefinedValue"]}`}</TableCell>
                                      <TableCell align="center">  {`${bsdd["bsdd"][domain][classification][result]['ifc_property_value']}`}</TableCell>
                                    </TableRow>
                                  </TableBody>
                                </Table>
                              </TableContainer>
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
    </TreeView></Paper>
  );
}