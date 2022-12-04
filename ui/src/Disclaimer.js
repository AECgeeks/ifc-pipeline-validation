
import {useEffect, useState} from 'react';
import { FETCH_PATH } from './environment'
import Link from '@mui/material/Link';

function Disclaimer(){
    return (
        <div class="sentence">Let us know what we're getting right and what we can improve at <Link href="mailto:validate@buildingsmart.org" underline="none">{'validate@buildingsmart.org'}</Link>
        </div>
    )
}

export default Disclaimer;