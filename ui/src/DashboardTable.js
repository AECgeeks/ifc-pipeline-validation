import * as React from 'react';
import PropTypes from 'prop-types';
import { alpha } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Checkbox from '@mui/material/Checkbox';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import DeleteIcon from '@mui/icons-material/Delete';
import FilterListIcon from '@mui/icons-material/FilterList';
import { visuallyHidden } from '@mui/utils';
import CircularStatic from "./CircularStatic";
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BrowserNotSupportedIcon from '@mui/icons-material/BrowserNotSupported';
import WarningIcon from '@mui/icons-material/Warning';
import Link from '@mui/material/Link';
import { FETCH_PATH } from './environment'
import { useEffect, useState } from 'react';

const statusToIcon = {
  "n": <BrowserNotSupportedIcon color="disabled" />,
  "v": <CheckCircleIcon color="success" />,
  "i": <ErrorIcon color="error" />,
  "w": <WarningIcon color="warning" />
}

function computeRelativeDates(modelDate) {
  var offset = modelDate.getTimezoneOffset();
  modelDate = new Date(
    Date.UTC(
      modelDate.getUTCFullYear(),
      modelDate.getUTCMonth(),
      modelDate.getUTCDate(),
      modelDate.getUTCHours(),
      modelDate.getUTCMinutes() - offset,
      modelDate.getUTCSeconds()
    )
  );

  var now = new Date();
  var difference = (now - modelDate) / 1000; // convert from ms to s
  let [divisor, unit] = [[3600 * 24 * 8, null], [3600 * 24 * 7, "weeks"], [3600 * 24, "days"], [3600, "hours"], [60, "minutes"], [1, "seconds"]].filter(a => difference / a[0] > 1.)[0];
  if (unit) {
    var relativeTime = Math.floor(difference / divisor);
    if (relativeTime == 1) { unit = unit.slice(0, -1); } // Remove the 's' in units if only 1
    return (<span class="abs_time" title={modelDate.toLocaleString()}>{relativeTime} {unit} ago</span>)
  } else {
    return modelDate.toLocaleString();
  }
}

function descendingComparator(a, b, orderBy) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

function getComparator(order, orderBy) {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

// This method is created for cross-browser compatibility, if you don't
// need to support IE11, you can use Array.prototype.sort() directly
function stableSort(array, comparator) {
  const stabilizedThis = array.map((el, index) => [el, index]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

const headCells = [
  {
    id: 'format',
    numeric: false,
    disablePadding: true,
    label: 'File format',
  },
  {
    id: 'filename',
    numeric: true,
    disablePadding: false,
    label: 'File name',
  },
  {
    id: 'syntax',
    numeric: true,
    disablePadding: false,
    label: 'Syntax',
  },
  {
    id: 'schema',
    numeric: true,
    disablePadding: false,
    label: 'Schema',
  },
  {
    id: 'bsdd',
    numeric: true,
    disablePadding: false,
    label: 'bSDD',
  },
  {
    id: 'ia',
    numeric: true,
    disablePadding: false,
    label: 'IA',
  },
  {
    id: 'ip',
    numeric: true,
    disablePadding: false,
    label: 'IP',
  },
  {
    id: 'report',
    numeric: true,
    disablePadding: false,
    label: '',
  },
  {
    id: 'date',
    numeric: true,
    disablePadding: false,
    label: '',
  },
  {
    id: 'download',
    numeric: true,
    disablePadding: false,
    label: '',
  }
];

function EnhancedTableHead(props) {
  const { onSelectAllClick, order, orderBy, numSelected, rowCount, onRequestSort } =
    props;
  const createSortHandler = (property) => (event) => {
    onRequestSort(event, property);
  };

  return (
    <TableHead>
      <TableRow>
        <TableCell padding="checkbox">
          <Checkbox
            color="primary"
            indeterminate={numSelected > 0 && numSelected < rowCount}
            checked={rowCount > 0 && numSelected === rowCount}
            onChange={onSelectAllClick}
            inputProps={{
              'aria-label': 'select all desserts',
            }}
          />
        </TableCell>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            align={headCell.numeric ? 'right' : 'left'}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            <TableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : 'asc'}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <Box component="span" sx={visuallyHidden}>
                  {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                </Box>
              ) : null}
            </TableSortLabel>
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

EnhancedTableHead.propTypes = {
  numSelected: PropTypes.number.isRequired,
  onRequestSort: PropTypes.func.isRequired,
  onSelectAllClick: PropTypes.func.isRequired,
  order: PropTypes.oneOf(['asc', 'desc']).isRequired,
  orderBy: PropTypes.string.isRequired,
  rowCount: PropTypes.number.isRequired,
};

function EnhancedTableToolbar(props) {
  const { numSelected } = props;

  return (
    <Toolbar
      sx={{
        pl: { sm: 2 },
        pr: { xs: 1, sm: 1 },
        ...(numSelected > 0 && {
          bgcolor: (theme) =>
            alpha(theme.palette.primary.main, theme.palette.action.activatedOpacity),
        }),
      }}
    >
      {numSelected > 0 ? (
        <Typography
          sx={{ flex: '1 1 100%' }}
          color="inherit"
          variant="subtitle1"
          component="div"
        >
          {numSelected} selected
        </Typography>
      ) : (
        <Typography
          sx={{ flex: '1 1 100%' }}
          variant="h6"
          id="tableTitle"
          component="div"
        >

        </Typography>
      )}

      {numSelected > 0 ? (
        <Tooltip title="Delete">
          <IconButton>
            <DeleteIcon />
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title="Filter list">
          <IconButton>
            <FilterListIcon />
          </IconButton>
        </Tooltip>
      )}
    </Toolbar>
  );
}

EnhancedTableToolbar.propTypes = {
  numSelected: PropTypes.number.isRequired,
};

export default function DashboardTable({models}) {
  const [rows, setRows] = React.useState([])
  const [order, setOrder] = React.useState('asc');
  const [orderBy, setOrderBy] = React.useState('');
  const [selected, setSelected] = React.useState([]);
  const [page, setPage] = React.useState(0);
  const [dense, setDense] = React.useState(false);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);
  const [count, setCount] = React.useState(0)
  const [validating, setValidated] = React.useState(false)

  useEffect(()=>{
      fetch(`${FETCH_PATH}/api/models_paginated/${page * rowsPerPage}/${page * rowsPerPage + rowsPerPage}`)
      .then((response) => response.json())
      .then((json) => {
        setRows(json["models"])
        setCount(json["count"])

        json["models"].map((m)=>{
          if(validating == true){
            setValidated(false)
          }else{
            setValidated(true )
          }
        })
      });
  },[page, rowsPerPage, validating]);


  const handleRequestSort = (event, property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleSelectAllClick = (event) => {
    if (event.target.checked) {
      const newSelected = rows.map((n) => n.id);
      setSelected(newSelected);
      return;
    }
    setSelected([]);
  };

  const handleClick = (event, filename) => {
    const selectedIndex = selected.indexOf(filename);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, filename);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
    }

    setSelected(newSelected);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeDense = (event) => {
    setDense(event.target.checked);
  };

  const isSelected = (name) => selected.indexOf(name) !== -1;

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <EnhancedTableToolbar numSelected={selected.length} />
        <TableContainer>
          <Table
            sx={{ minWidth: 750 }}
            aria-labelledby="tableTitle"
            size={dense ? 'small' : 'medium'}
          >
            <EnhancedTableHead
              numSelected={selected.length}
              order={order}
              orderBy={orderBy}
              onSelectAllClick={handleSelectAllClick}
              onRequestSort={handleRequestSort}
              rowCount={rows.length}
            />
            <TableBody>
              {/* if you don't need to support IE11, you can replace the `stableSort` call with:
                 rows.sort(getComparator(order, orderBy)).slice() */}
              {stableSort(rows, getComparator(order, orderBy))
                .map((row, index) => {
                  const isItemSelected = isSelected(row.id);
                  const labelId = `enhanced-table-checkbox-${index}`;
                  if (row.progress == 100) {
                    return (
                      <TableRow
                        hover
                        onClick={(event) => handleClick(event, row.id)}
                        role="checkbox"
                        aria-checked={isItemSelected}
                        tabIndex={-1}
                        key={row.id}
                        selected={isItemSelected}
                      >
                        <TableCell padding="checkbox">
                          <Checkbox
                            color="primary"
                            checked={isItemSelected}
                            inputProps={{
                              'aria-labelledby': labelId,
                            }}
                          />
                        </TableCell>
                        <TableCell
                          component="th"
                          id={labelId}
                          scope="row"
                          padding="none"
                        >
                          IFC
                        </TableCell>
                        <TableCell align="right">{row.filename}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_syntax]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_schema]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_bsdd]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_ia]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_ip]}</TableCell>
                        <TableCell align="right">
                          <Link href={`/report/${row.code}`} underline="hover">
                            {'View report'}
                          </Link>
                        </TableCell>
                        <TableCell align="right">{computeRelativeDates(new Date(row.date))}</TableCell>
                        <TableCell align="right">
                          <Link href={`${FETCH_PATH}/api/download/${row.id}`} underline="hover">
                            {'Download file'}
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  } else {
                    
                    return (
                      <TableRow
                        hover
                        onClick={(event) => handleClick(event, row.id)}
                        role="checkbox"
                        aria-checked={isItemSelected}
                        tabIndex={-1}
                        key={row.id}
                        selected={isItemSelected}
                      >
                        <TableCell padding="checkbox">
                          <Checkbox
                            color="primary"
                            checked={isItemSelected}
                            inputProps={{
                              'aria-labelledby': labelId,
                            }}
                          />
                        </TableCell>
                        <TableCell
                          component="th"
                          id={labelId}
                          scope="row"
                          padding="none"
                        >
                          IFC
                        </TableCell>
                        <TableCell align="right">{row.filename}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_syntax]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_schema]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_bsdd]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_ia]}</TableCell>
                        <TableCell align="right">{statusToIcon[row.status_ip]}</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"><CircularStatic value={row.progress} /></TableCell>
                        <TableCell align="right">
                          <Link href={`${FETCH_PATH}/api/download/${row.id}`} underline="hover">
                            {'Download file'}
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  }
                })}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={count}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={ (event) => {setRowsPerPage(parseInt(event.target.value, 10))}}
        />
      </Paper>
      <FormControlLabel
        control={<Switch checked={dense} onChange={handleChangeDense} />}
        label="Dense padding"
      />
    </Box>
  );
}