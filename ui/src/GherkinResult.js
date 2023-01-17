import * as React from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';
import { statusToColor } from './mappings'

function GherkinResults({ status, gherkin_task, task_type }) {

    if (gherkin_task.results.length > 0) {
        return (
            <div>
                <TreeView
                    aria-label="file system navigator"
                    defaultCollapseIcon={<ExpandMoreIcon />}
                    defaultExpandIcon={<ChevronRightIcon />}
                    defaultExpanded={["0"]}
                    sx={{ "width": "850px", "backgroundColor": statusToColor[status] }}
                >
                    <TreeItem nodeId="0" label={task_type}>
                        {
                            gherkin_task.results.map((result) => {

                                return (
                                    <div>
                                        <a href={result.feature_url}>{result.feature}</a> <br></br>
                                        <b>{result.step}</b>
                                        <div>{result.message}</div>
                                        <br></br>
                                        <br></br>
                                    </div>
                                )
                            }
                            )
                        }
                    </TreeItem>
                </TreeView>
            </div>
        )
    }
    else {
        return (
            <div>
                <TreeView
                    aria-label="file system navigator"
                    defaultCollapseIcon={<ExpandMoreIcon />}
                    defaultExpandIcon={<ChevronRightIcon />}
                    defaultExpanded={["0"]}
                    sx={{ "width": "850px", "backgroundColor": statusToColor[status] }}
                >
                    <TreeItem nodeId="0" label={task_type}>
                        <pre>{"Not checked"}</pre>
                    </TreeItem>
                </TreeView>
            </div>
        )

    }

}


export default GherkinResults