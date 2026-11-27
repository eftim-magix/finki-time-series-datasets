"""Run from datasets/mepso/scripts with: python3 -m unittest test_process_mepso.py"""
import argparse
import contextlib
import csv
import datetime as dt
import io
from pathlib import Path
import shutil
import tempfile
import unittest

import process_mepso as importer

SOURCE = Path(__file__).resolve().parents[1]/'raw'   # datasets/mepso/raw


class ImportTests(unittest.TestCase):
    def test_reference_changes_without_reparsing(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            original=next(SOURCE.rglob('*2020-01_final.xlsx'))
            shutil.copyfile(original,base/original.name)
            args=argparse.Namespace(input=base,output=None,state=None,start=None,end=None,rebuild=False)
            def reference(price):
                with (base/'applied_price_references.csv').open('w',newline='') as handle:
                    writer=csv.writer(handle)
                    writer.writerow(['timestamp_utc','reference_price_eur_per_mwh','reference_filename','reference_cell'])
                    writer.writerow(['2019-12-31T23:00:00Z',price,'reference.xlsx','Settlement!J11'])
            with contextlib.redirect_stdout(io.StringIO()):
                importer.run(args)
                reference(44.70019209659715)
                result=importer.run(args)
                self.assertEqual(result['parsed_files'],0)
                with (base/'MEPSO_balancing_prices_hourly.csv').open() as handle:
                    row=next(csv.DictReader(handle))
                self.assertEqual(row['final_applied_price_status'],'matched_settlement_reference')
                self.assertAlmostEqual(float(row['final_price_applied_eur_per_mwh']),44.70019209659715)
                reference(999999)
                result=importer.run(args)
                self.assertEqual(result['parsed_files'],0)
                with (base/'MEPSO_balancing_prices_hourly.csv').open() as handle:
                    row=next(csv.DictReader(handle))
                self.assertEqual(row['final_price_applied_eur_per_mwh'],'')
                self.assertEqual(row['final_applied_price_status'],'reference_mismatch')

    def test_applied_price_selection_and_revision_isolation(self):
        select=importer.select_applied_price
        self.assertEqual(select({'final_price_wapneg_eur_per_mwh':-25},'final')[:2],(-25,'wapneg'))
        self.assertEqual(select({'final_price_wappos_eur_per_mwh':0},'final')[0],0)
        self.assertIsNone(select({'preliminary_price_wappos_eur_per_mwh':100},'final')[0])
        pair={'final_price_vaa_plus_eur_per_mwh':45,'final_price_vaa_minus_eur_per_mwh':135,
              **{f'final_{r}_{d}_mwh':0 for r in ['afrr','mfrr'] for d in ['up','down']}}
        self.assertEqual(select(pair,'final')[2],'ambiguous_fallback')
        self.assertEqual(select(pair,'final',{'price':135})[:2],(135,'vaa_minus'))
        self.assertEqual(select(pair,'final',{'price':136})[2],'reference_mismatch')
        legacy={'final_price_wappos_eur_per_mwh':70,'final_price_wapneg_eur_per_mwh':0,
                'final_afrr_net_mwh':3,'final_mfrr_net_mwh':-1}
        self.assertEqual(select(legacy,'final')[:2],(70,'wappos'))
        legacy['final_price_wapneg_eur_per_mwh']=40
        self.assertEqual(select(legacy,'final')[2],'ambiguous_multiple_directional_prices')
        self.assertIsNone(select({},'final')[0])


    def test_utc_offsets_and_spring_gap(self):
        self.assertEqual(importer.utc_hour(dt.date(2026,1,1),1), '2025-12-31T23:00:00Z')
        self.assertEqual(importer.utc_hour(dt.date(2026,7,1),1), '2026-06-30T22:00:00Z')
        self.assertIsNone(importer.utc_hour(dt.date(2026,3,29),3))
        self.assertEqual(importer.utc_hour(dt.date(2026,3,29),4), '2026-03-29T01:00:00Z')

    def test_fall_fold_and_hour_labels(self):
        day = dt.date(2026,10,25)
        self.assertEqual(importer.utc_hour(day,3,0), '2026-10-25T00:00:00Z')
        self.assertEqual(importer.utc_hour(day,3,1), '2026-10-25T01:00:00Z')
        self.assertIsNone(importer.utc_hour(dt.date(2026,10,24),3,1))
        for label in ['H3B','Н3В','3Bh']:
            self.assertEqual(importer.hour_label(label), (3,1))

    def test_mixed_supplement_separates_currencies_and_services(self):
        path = next(SOURCE.rglob('*2021-10_final_2021-10-31.xlsx'))
        result = importer.parse_workbook(path)
        self.assertEqual(len(result['rows']),25)
        row = result['rows']['2021-10-31T00:00:00Z']
        repeated = result['rows']['2021-10-31T01:00:00Z']
        self.assertEqual(row['price_wappos_eur_per_mwh'],123.625)
        self.assertEqual(repeated['price_wappos_eur_per_mwh'],104.035)
        self.assertAlmostEqual(row['price_wappos_mkd_per_mwh'],7624.5842375)
        self.assertTrue({'afrr_up_mwh','mfrr_up_mwh'} <= set(row))
        self.assertEqual(row['mfrr_up_mwh'],10)
        self.assertIn('ace_mwh_per_h',result['metrics'])
        # This supplement's ACE cells are blank: never turn its daily total 0 into hourly data.
        self.assertNotIn('ace_mwh_per_h',row)

    def test_imbalance_price_regimes(self):
        prices = {'final_price_wappos_eur_per_mwh': 120.0, 'final_price_wapneg_eur_per_mwh': None,
                  'final_price_vaa_plus_eur_per_mwh': 0, 'final_price_vaa_minus_eur_per_mwh': 0}
        # System short (more upward than downward energy): WAPpos for surplus and deficit alike.
        row = dict(prices, final_afrr_up_mwh=5.0, final_afrr_down_mwh=-2.0, final_mfrr_up_mwh=0)
        self.assertEqual(importer.imbalance_prices(row, 'final'), ('wappos', 120.0, 120.0, []))
        # Downward energy published as positive still counts as downward.
        row = {'final_price_wapneg_eur_per_mwh': -10.0, 'final_afrr_up_mwh': 1.0, 'final_afrr_down_mwh': 3.0}
        self.assertEqual(importer.imbalance_prices(row, 'final')[:3], ('wapneg', -10.0, -10.0))
        # No activation: dual VAA price, VAA+ for a surplus, VAA- for a deficit.
        row = {'final_price_vaa_plus_eur_per_mwh': 45.37, 'final_price_vaa_minus_eur_per_mwh': 136.11,
               'final_afrr_up_mwh': 0, 'final_afrr_down_mwh': 0, 'final_mfrr_up_mwh': 0, 'final_mfrr_down_mwh': 0}
        self.assertEqual(importer.imbalance_prices(row, 'final'), ('vaa', 45.37, 136.11, []))
        # Without activation data the single non-zero component decides, and is flagged.
        row = {'preliminary_price_wapneg_eur_per_mwh': 30.0, 'preliminary_price_wappos_eur_per_mwh': 0}
        self.assertEqual(importer.imbalance_prices(row, 'preliminary'),
                         ('wapneg', 30.0, 30.0, ['preliminary_imbalance_regime_from_prices']))
        row = {'final_price_wappos_eur_per_mwh': 50.0, 'final_price_wapneg_eur_per_mwh': 40.0}
        self.assertEqual(importer.imbalance_prices(row, 'final'), (None, None, None, ['final_imbalance_regime_ambiguous']))
        self.assertEqual(importer.imbalance_prices({}, 'final'), (None, None, None, []))
        # Selected component blank: regime kept, price missing and flagged.
        row = {'final_price_wapneg_eur_per_mwh': 25.0, 'final_afrr_up_mwh': 4.0}
        self.assertEqual(importer.imbalance_prices(row, 'final'),
                         ('wappos', None, None, ['final_imbalance_price_component_missing', 'final_imbalance_unselected_component_nonzero']))

    def test_incremental_add_replace_remove_and_missing_months(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            original=next(SOURCE.rglob('*2020-01_final.xlsx'))
            path=base/original.name
            shutil.copyfile(original,path)
            args=argparse.Namespace(input=base,output=None,state=None,start='2020-01',end='2020-02',rebuild=False)
            with contextlib.redirect_stdout(io.StringIO()):
                first=importer.run(args)
                digest=importer.hashlib.sha256((base/'MEPSO_balancing_prices_hourly.csv').read_bytes()).hexdigest()
                second=importer.run(args)
                self.assertEqual(second['parsed_files'],0)
                self.assertEqual(second['reused_files'],1)
                self.assertEqual(digest,importer.hashlib.sha256((base/'MEPSO_balancing_prices_hourly.csv').read_bytes()).hexdigest())
                preliminary=next(SOURCE.rglob('*2020-01_preliminary.xlsx'))
                shutil.copyfile(preliminary,base/preliminary.name)
                third=importer.run(args)
                self.assertEqual((third['parsed_files'],third['reused_files']),(1,1))
                # A changed existing filename must be reparsed, even if its month is old.
                shutil.copyfile(preliminary,path)
                fourth=importer.run(args)
                self.assertEqual((fourth['parsed_files'],fourth['reused_files']),(1,1))
                path.unlink()
                fifth=importer.run(args)
                self.assertEqual(len(fifth['removed_files']),1)
            self.assertEqual(first['rows'],(31+29)*24)
            self.assertEqual(first['status_counts']['missing'],29*24)
            with (base/'MEPSO_balancing_prices_hourly.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(rows[-1]['status'],'missing')
            self.assertEqual(rows[-1]['final_price_wappos_eur_per_mwh'],'')
            # Only the preliminary source remains after the removals above.
            self.assertIn(rows[0]['imbalance_regime'],{'wappos','wapneg','vaa'})
            self.assertEqual(rows[0]['imbalance_price_version'],'preliminary')
            self.assertEqual(rows[-1]['imbalance_price_surplus_eur_per_mwh'],'')


if __name__=='__main__':
    unittest.main()
