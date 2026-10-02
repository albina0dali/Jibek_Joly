import {useSyncExternalStore} from 'react';
import dictionary from './locales/catalog.json';
import resourceDictionary from './locales/resources.json';

export type Language='ru'|'kk'|'en';
const saved=localStorage.getItem('jibek-joly.language');
let current:Language=saved==='kk'||saved==='en'?saved:'ru';
const listeners=new Set<()=>void>();
const catalog={...dictionary,...resourceDictionary} as Record<string,string[]>;
const insensitive=new Map(Object.keys(catalog).map(k=>[k.toLowerCase(),k]));
document.documentElement.lang=current;
export function setLanguage(language:Language){current=language;localStorage.setItem('jibek-joly.language',language);document.documentElement.lang=language;listeners.forEach(fn=>fn())}
export function useLanguage(){return useSyncExternalStore(fn=>{listeners.add(fn);return()=>listeners.delete(fn)},()=>current)}
export function t(text:string|null|undefined):string{
 if(!text)return '';
 if(current==='en')return text.replaceAll('&lt;','<');
 const exact=catalog[text]||catalog[insensitive.get(text.toLowerCase())||''];
 if(exact)return exact[current==='ru'?0:1];
 const localized=(key:string)=>catalog[key]?.[current==='ru'?0:1]||key;
 let result=text;
 const patterns:[RegExp,(...args:string[])=>string][]=[
  [/^Priority-weighted delay ([\d.]+) min$/,(_,n)=>current==='ru'?`Задержка с учётом приоритета: ${n} мин`:`Басымдық ескерілген кідіріс: ${n} мин`],
  [/^(\d+)\/(\d+) services moving; target utilization 70%$/,(_,n,total)=>current==='ru'?`В движении ${n} из ${total}; целевая загрузка 70%`:`${total} пойыздың ${n}-і қозғалыста; мақсатты жүктеме 70%`],
  [/^Mean advisory energy saving ([\d.]+)% over full-power baseline$/,(_,n)=>current==='ru'?`Средняя расчётная экономия энергии: ${n}%`:`Орташа есептік энергия үнемі: ${n}%`],
  [/^(\d+) unresolved resource conflicts$/,(_,n)=>current==='ru'?`Неразрешённых ресурсных конфликтов: ${n}`:`Шешілмеген ресурс қайшылықтары: ${n}`],
  [/^Mean projected arrival deviation ([\d.]+) min$/,(_,n)=>current==='ru'?`Среднее отклонение прибытия: ${n} мин`:`Келудің орташа ауытқуы: ${n} мин`],
  [/^(\d+) events in this session$/,(_,n)=>current==='ru'?`Событий в сеансе: ${n}`:`Сеанстағы оқиғалар: ${n}`],
  [/^(\d+) services · updated once per second$/,(_,n)=>current==='ru'?`${n} поездов · обновление каждую секунду`:`${n} пойыз · секунд сайын жаңартылады`],
  [/^(\d+) scheduled services$/,(_,n)=>current==='ru'?`Запланировано поездов: ${n}`:`Жоспарланған пойыздар: ${n}`],
  [/^Proceed toward (S\d+) at ([\d.]+) km\/h$/,(_,station,speed)=>current==='ru'?`Следовать к ${station} со скоростью ${speed} км/ч`:`${station} бағытына ${speed} км/сағ жылдамдықпен жүру`],
  [/^Hold at ([\d.]+) km until (\d+)s$/,(_,km,sec)=>current==='ru'?`Ожидать на отметке ${km} км до ${sec} с модельного времени`:`${km} км белгісінде модель уақытының ${sec} секундына дейін күту`],
  [/^Weights total: ([\d.]+)% \(required: 100%\)$/,(_,n)=>current==='ru'?`Сумма весов: ${n}% (требуется 100%)`:`Салмақтар қосындысы: ${n}% (100% болуы керек)`],
  [/^Seed 42 scenario initialized; 15-minute warm-up recorded$/,()=>current==='ru'?'Сценарий seed 42 запущен; записан 15-минутный прогрев':'Seed 42 сценарийі іске қосылды; 15 минуттық дайындық жазылды'],
  [/^Injected (\w+) at (\w+)$/,(_,kind,location)=>current==='ru'?`Добавлено: ${t(kind.replaceAll('_',' '))}, ${location}`:`Қосылды: ${t(kind.replaceAll('_',' '))}, ${location}`],
  [/^Replanning finished: (\d+) verified alternatives, (\d+) ms$/,(_,n,ms)=>current==='ru'?`Перепланирование завершено: проверенных вариантов ${n}, ${ms} мс`:`Қайта жоспарлау аяқталды: тексерілген нұсқа ${n}, ${ms} мс`],
  [/^Applied to simulator: (.+); zero hard conflicts$/,(_,name)=>current==='ru'?`Применено в симуляторе: ${t(name)}; жёстких конфликтов нет`:`Симуляторда қолданылды: ${t(name)}; қатаң қайшылық жоқ`],
  [/^Admin updated simulator, Quality Index and optimization settings$/,()=>current==='ru'?'Администратор изменил параметры симуляции, качества и оптимизации':'Әкімші симуляция, сапа және оңтайландыру баптауларын өзгертті'],
  [/^(yard|fleet|maintenance) optimization computed; (\d+) ms; synthetic resources$/,(_,module,ms)=>current==='ru'?`Оптимизация ${t(module)} рассчитана; ${ms} мс; синтетические ресурсы`:`${t(module)} оңтайландыруы есептелді; ${ms} мс; синтетикалық ресурстар`],
  [/^Applied synthetic (yard|fleet|maintenance) resource plan (.+)$/,(_,module,id)=>current==='ru'?`Применён синтетический ресурсный план ${t(module)}: ${id}`:`Синтетикалық ресурс жоспары қолданылды ${t(module)}: ${id}`],
 ];
 for(const [pattern,replace] of patterns)if(pattern.test(result))return result.replace(pattern,replace);
 // Dynamic operational sentences use known fragments; identifiers and numbers remain intact.
 const fragments:Record<string,[string,string]>={
 'have incompatible occupation of':['имеют несовместимое занятие блока','блокты қатар иелене алмайды'],
 'trains require':['поездов требуют','пойызға қажет'], 'platforms at':['платформ на станции','станциясындағы платформалар'],
 'enters':['входит в','кіреді'], 'before the':['до истечения','аяқталмай тұрып'], 'clearance after':['интервала после','кейінгі аралық'],
 'requires':['требует','қажет етеді'], 'during':['во время','кезінде'], 'and':['и','және'],
 'priority':['приоритет','басымдық'], 'hold':['ожидать','күту'], 'min at km':['мин на отметке км','мин, км белгісінде'],
 'before':['перед','алдында'], 'arrival deviation':['отклонение прибытия','келу ауытқуы'],
 'expected':['ожидается','күтіледі'], 'projected':['прогноз','болжам'], 'arrival':['прибытие','келу'],
 'Effective':['Начало','Басталуы'], 'duration':['длительность','ұзақтығы'], 'Select':['Выбрать','Таңдау'],
 'showing the last received state. Automatic reconnect is active.':['показано последнее состояние. Переподключение выполняется автоматически.','соңғы күй көрсетілген. Қайта қосылу автоматты түрде орындалады.'],
 'Simulation estimate · arbitrary energy units':['Оценка симуляции · условные единицы энергии','Симуляция бағасы · шартты энергия бірліктері'],
 'Select a trajectory to inspect its resource schedule. Horizontal segments indicate station dwell.':['Выберите траекторию. Горизонтальные участки показывают стоянку на станции.','Траекторияны таңдаңыз. Көлденең бөліктер станциядағы тұру уақытын көрсетеді.'],
 'Current schedule satisfies all resource constraints; no additional holds required.':['Текущий план удовлетворяет ресурсным ограничениям; дополнительные остановки не нужны.','Ағымдағы жоспар ресурс шектеулерін сақтайды; қосымша тоқтау қажет емес.'],
 'Retain the current feasible resource ordering.':['Сохранить текущий допустимый порядок движения.','Ағымдағы рұқсат етілген қозғалыс ретін сақтау.'],
 };
 for(const [key,value] of Object.entries(fragments).sort((a,b)=>b[0].length-a[0].length))result=result.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'g'),value[current==='ru'?0:1]);
 // These are physical units and status values, not translated resource IDs.
 result=result.replace(/\bkm\/h\b/g,localized('km/h')).replace(/\bmin\b/g,localized('min')).replace(/\bkm\b/g,localized('km'));
 return result;
}
export function LanguageSwitcher(){const language=useLanguage();return <div className="language-switch" aria-label="Language / Язык / Тіл">{(['ru','kk','en'] as Language[]).map(value=><button key={value} type="button" aria-label={{ru:'Русский',kk:'Қазақша',en:'English'}[value]} aria-pressed={language===value} onClick={()=>setLanguage(value)}>{value==='kk'?'ҚАЗ':value.toUpperCase()}</button>)}</div>}
