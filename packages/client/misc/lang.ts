import { t as tt, ngettext, msgid as tmsgid } from 'ttag';

export const t = tt;
export default t;

export const pluralize = ngettext;
export const msgid = tmsgid;

// Example
// pluralize(msgid`${i} tick passed`, `${i} ticks passed`, i)
