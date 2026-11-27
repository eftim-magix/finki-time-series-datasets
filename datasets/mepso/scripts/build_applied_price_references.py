"""Extract explicit applied-price evidence from a plant Settlement workbook."""
import argparse,csv,datetime as dt,hashlib,re
from pathlib import Path
import openpyxl
from process_mepso import utc_hour,number,atomic_write

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'raw'/'applied_price_references.csv')
    parser.add_argument('--label',help='Name stored instead of the workbook filename (the filename names the plant); default plant_settlement_<YYYY-MM>.xlsx')
    args=parser.parse_args()
    wb=openpyxl.load_workbook(args.workbook,read_only=True,data_only=True)
    records=[];seen=set()
    try:
        ws=wb['Settlement'];rate=ws['B10'].value
        if ws['J1'].value!='MEPSO Price' or ws['J10'].value!='MKD/kWh' or not number(rate) or rate<=0:
            raise ValueError('Unexpected workbook price header, units or conversion rate')
        digest=hashlib.sha256(args.workbook.read_bytes()).hexdigest()
        for i,row in enumerate(ws.values,1):
            date,hour,price=row[6],row[7],row[9]
            if not isinstance(date,dt.datetime) or not isinstance(hour,str):continue
            match=re.fullmatch(r'H(\d{1,2})(B?)',hour)
            if not match:continue
            if not number(price):raise ValueError(f'Missing/non-numeric reference at J{i}')
            timestamp=utc_hour(date.date(),int(match[1]),int(bool(match[2])))
            if timestamp is None or timestamp in seen:raise ValueError(f'Invalid/duplicate reference hour at row {i}')
            seen.add(timestamp)
            records.append(dict(timestamp_utc=timestamp,reference_price_eur_per_mwh=price*1000/rate,
                                reference_filename=None,reference_cell=f'Settlement!J{i}',
                                reference_rate_mkd_per_eur=rate,reference_workbook_sha256=digest))
    finally:wb.close()
    if not records:raise ValueError('No reference observations found')
    month=max(records,key=lambda r:r['timestamp_utc'])['timestamp_utc'][:7]
    for r in records:r['reference_filename']=args.label or f'plant_settlement_{month}.xlsx'
    def write(handle):
        writer=csv.DictWriter(handle,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    atomic_write(args.output,write)
    print(f'Wrote {len(records)} applied-price reference observations')

if __name__=='__main__':main()
