import {t as tr} from './i18n';

export function PageTitle({eyebrow,title,description,action}:{eyebrow:string;title:string;description:string;action?:React.ReactNode}){return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{tr(title)}</h1><p>{tr(description)}</p></div>{action}</div>}
