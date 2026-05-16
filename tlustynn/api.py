"""
High-level API for TLUSTY NN atmosphere prediction.

Usage:
    from tlustynn import predict_atmosphere

    df = predict_atmosphere(teff=10000, logg=3.7, mh=0.0)
    # Returns a pandas DataFrame with columns:
    # teff, logg, mh, tau, T, ne, rho, level_1 ... level_55
"""

import os
import numpy as np
import pandas as pd

from .predict import TlustyPredictor


# Singleton predictor instance (lazy initialization)
_predictor = None


def _get_predictor():
    """Get or create the default TlustyPredictor."""
    global _predictor
    if _predictor is None:
        _predictor = TlustyPredictor()
    return _predictor


def write_tlusty_model7(filename, model_data):

    df = model_data['dataframe']
    n_depth = model_data['n_depth']
    n_params = model_data['n_params']
    
    with open(filename, 'w') as f:
        # Write header: number of depths and parameters
        f.write(f"   {n_depth:3d}   {n_params:3d}\n")
        
        # Write tau values (first parameter column)
        tau_values = df['tau'].values
        for i in range(0, n_depth, 6):
            line_values = tau_values[i:i+6]
            line_str = "".join(f" {val:13.6E}" for val in line_values)
            f.write(line_str + "\n")
        
        # Write all other parameters for each depth
        for depth_idx in range(n_depth):
            row_data = df.iloc[depth_idx, 2:].values  # Skip teff, logg, mh
            
            for i in range(0, n_params, 6):
                line_values = row_data[i:i+6]
                line_str = "  " + "".join(f" {val:13.6E}" for val in line_values)
                f.write(line_str + "\n")



def create_tlusty_input(output_path, teff, logg, lte_flag, ltgray_flag, nst_mode, nfread, natoms, modes, ions):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if nst_mode==None:

        with open(output_path, 'w') as f:
            f.write(f" {teff:.0f}  {logg}      ! TEFF, GRAV\n")  # 改为保留2位小数
            f.write(f" {lte_flag}  {ltgray_flag}                ! LTE,  LTGRAY\n")
            f.write(f" ''                  ! no change of general optional parameters\n")
            f.write("*\n")
            f.write("* frequencies\n")
            f.write("*\n")
            f.write(f" {nfread:3d}                  ! NFREAD\n")
            f.write("*" + "-" * 64 + "\n")
            f.write("* data for atoms   \n")
            f.write("*\n")
            f.write(f" {natoms:2d}                   ! NATOMS\n")
            f.write("* mode abn modpf\n")
       

            for mode, abn, modpf in modes:
                # 修复：根据abn的类型使用不同的格式化方式
                if isinstance(abn, float):
                    f.write(f"   {mode:>2d}  {abn:>6.2f}      {modpf:>2d}\n")
                else:
                    f.write(f"   {mode:>2d}  {abn:>2d}      {modpf:>2d}\n")


            f.write("*" + "-" * 64 + "\n")
            f.write("* data for ions\n")
            f.write("*\n")
            f.write("*iat   iz   nlevs  ilast ilvlin  nonstd typion  filei\n")
            f.write("*\n")
            

            for ion_data in ions:
                iat, iz, nlevs, ilast, ilvlin, nonstd, typion, filei = ion_data
                
                if iat == 0 and iz == 0 and nlevs == "" and ilast == "" and ilvlin == "" and nonstd == "" and typion == "":
                    filei_str = " " * 38 + f"'{filei}'" 
                    f.write(f"   0    0{filei_str}\n")
                else:
                    # 修复：根据值的类型使用不同的格式化方式
                    iat_str = "  " if iat == "" else f"{int(iat):3d}"
                    iz_str = "  " if iz == "" else f"{int(iz):2d}"
                    
                    # 处理可能为空的字段
                    if nlevs == "":
                        nlevs_str = "     "
                    else:
                        nlevs_str = f"{int(nlevs):5d}"
                    
                    if ilast == "":
                        ilast_str = "     "
                    else:
                        ilast_str = f"{int(ilast):6d}"
                    
                    if ilvlin == "":
                        ilvlin_str = "      "
                    else:
                        ilvlin_str = f"{int(ilvlin):6d}"
                    
                    if nonstd == "":
                        nonstd_str = "       "
                    else:
                        nonstd_str = f"{int(nonstd):6d}"
                    
                    typion_str = "       " if typion == "" else f"'{typion}'"
                    filei_str = "       " if filei == "" else f"'{filei}'"

                    if all(x == "" for x in [iat, iz, nlevs, ilast, ilvlin, nonstd, typion, filei]):
                        f.write(" \n")
                    else:
                        line = f" {iat_str}   {iz_str} {nlevs_str} {ilast_str} {ilvlin_str} {nonstd_str}    {typion_str} {filei_str}\n"
                        f.write(line)

            f.write("*\n")
            f.write("* end\n")
    else:
        with open(output_path, 'w') as f:
            f.write(f" {teff:.0f}  {logg}      ! TEFF, GRAV\n")
            f.write(f" {lte_flag}  {ltgray_flag}                ! LTE,  LTGRAY\n")
            f.write(f" '{nst_mode}'                  ! no change of general optional parameters\n")
            f.write("*" + "-" * 64 + "\n")
            f.write("* frequencies\n")
            f.write("*\n")
            f.write(f" {nfread:3d}                  ! NFREAD\n")
            f.write("*" + "-" * 64 + "\n")
            f.write("* data for atoms   \n")
            f.write("*\n")
            f.write(f" {natoms:2d}                   ! NATOMS\n")
            f.write("* mode abn modpf\n")
            
            for mode, abn, modpf in modes:
                # 修复：根据abn的类型使用不同的格式化方式
                if isinstance(abn, float):
                    f.write(f"   {mode:>2d}  {abn:>6.2f}      {modpf:>2d}\n")
                else:
                    f.write(f"   {mode:>2d}  {abn:>2d}      {modpf:>2d}\n")


            f.write("*" + "-" * 64 + "\n")
            f.write("* data for ions\n")
            f.write("*\n")
            f.write("*iat   iz   nlevs  ilast ilvlin  nonstd typion  filei\n")
            f.write("*\n")
            
            for ion_data in ions:
                iat, iz, nlevs, ilast, ilvlin, nonstd, typion, filei = ion_data
                
                if iat == 0 and iz == 0 and nlevs == "" and ilast == "" and ilvlin == "" and nonstd == "" and typion == "":
                    filei_str = " " * 38 + f"'{filei}'" 
                    f.write(f"   0    0{filei_str}\n")
                else:
                    # 修复：根据值的类型使用不同的格式化方式
                    iat_str = "  " if iat == "" else f"{int(iat):3d}"
                    iz_str = "  " if iz == "" else f"{int(iz):2d}"
                    
                    # 处理可能为空的字段
                    if nlevs == "":
                        nlevs_str = "     "
                    else:
                        nlevs_str = f"{int(nlevs):5d}"
                    
                    if ilast == "":
                        ilast_str = "     "
                    else:
                        ilast_str = f"{int(ilast):6d}"
                    
                    if ilvlin == "":
                        ilvlin_str = "      "
                    else:
                        ilvlin_str = f"{int(ilvlin):6d}"
                    
                    if nonstd == "":
                        nonstd_str = "       "
                    else:
                        nonstd_str = f"{int(nonstd):6d}"
                    
                    typion_str = "       " if typion == "" else f"'{typion}'"
                    filei_str = "       " if filei == "" else f"'{filei}'"

                    if all(x == "" for x in [iat, iz, nlevs, ilast, ilvlin, nonstd, typion, filei]):
                        f.write(" \n")
                    else:
                        line = f" {iat_str}   {iz_str} {nlevs_str} {ilast_str} {ilvlin_str} {nonstd_str}    {typion_str} {filei_str}\n"
                        f.write(line)

            f.write("*\n")
            f.write("* end\n")



def create_ff_model(output_dir, teff, logg, mh, lte_flag, ltgray_flag, nstmode, frequency, natoms_num):
    os.makedirs(output_dir, exist_ok=True)
    
    if mh == 0:
        mh_str = f"{mh:.1f}"
        filename = f"{teff}_{logg}_{mh_str}.5"
        output_path = os.path.join(output_dir, filename)



        modes = []
        elements = [
            (2, 0, 0),  # H
            (2, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (1, 0, 0),
            (1, 0, 0),
            (1, 0, 0)
            ]
        
        modes.extend(elements)
        
        ions = [
            ( 1,   0,   9,   0,   0,   0, ' H 1', 'data/h1.dat'),
            ( 1,   1,   1,   1,   0,   0, ' H 2', ' '),
            ( 2,   0,  24,   0,   0,   0, 'He 1', 'data/he1.dat'),
            ( 2,   1,  20,   0,   0,   0, 'He 2', 'data/he2.dat'),
            ( 2,   2,   1,   1,   0,   0, 'He 3', ' '),
            ( 0,   0,   0,  -1,   0,   0, '    ', ' ')
            ]
        
        create_tlusty_input(output_path, teff, logg, lte_flag, ltgray_flag, nstmode, frequency, natoms_num, modes, ions)



    else:
        mh_str = f"{mh:.1f}"
        filename = f"{teff}_{logg}_{mh_str}.5"
        output_path = os.path.join(output_dir, filename)
            
        modes = []
        elements = [
            (2, 0, 0),  # H
            (2, mh, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (1, 0, 0),
            (1, 0, 0),
            (1, 0, 0)
            ]
        
        modes.extend(elements)
        
        ions = [
            ( 1,   0,   9,   0,   0,   0, ' H 1', 'data/h1.dat'),
            ( 1,   1,   1,   1,   0,   0, ' H 2', ' '),
            ( 2,   0,  24,   0,   0,   0, 'He 1', 'data/he1.dat'),
            ( 2,   1,  20,   0,   0,   0, 'He 2', 'data/he2.dat'),
            ( 2,   2,   1,   1,   0,   0, 'He 3', ' '),
            ( 0,   0,   0,  -1,   0,   0, '    ', ' ')
            ]
        
        create_tlusty_input(output_path, teff, logg, lte_flag, ltgray_flag, nstmode, frequency, natoms_num, modes, ions)


def predict_atmosphere(teff, logg, mh, output_dir=None, filename=None, output_format='csv'):
    """Predict a single stellar atmosphere model and optionally save to file.

    The output follows the same column order as ``hhe.csv``:
    ``teff, logg, mh, tau, T, ne, rho, level_1, ..., level_55``.
    Each model contains 50 depth rows.

    Parameters
    ----------
    teff : float
        Effective temperature [K].
    logg : float
        Surface gravity (log10 of cm s^-2).
    mh : float
        Metallicity [dex].
    output_dir : str, optional
        Directory where the output file will be written. If ``None``, the DataFrame
        is returned but no file is written.
    filename : str, optional
        Explicit file name. If ``None``, the file is named ``{teff}_{logg}_{mh}.{ext}``.
    output_format : str, optional
        Output format: 'csv' or '7' (TLUSTY format). Default is 'csv'.

    Returns
    -------
    pandas.DataFrame
        DataFrame with 50 rows (one per atmospheric depth) and columns
        matching the original ``hhe.csv`` format.
    str or None
        Absolute path to the saved file if ``output_dir`` is given,
        otherwise ``None``.
    """
    predictor = _get_predictor()
    result = predictor.predict(teff, logg, mh)
    y_pred = result['prediction'][0]  # [50, n_outputs]

    # Retrieve output column names from training stats
    if predictor.stats and 'output_cols' in predictor.stats:
        output_cols = predictor.stats['output_cols']
    else:
        output_cols = [f'col_{i}' for i in range(y_pred.shape[1])]

    # Build DataFrame from prediction
    df = pd.DataFrame(y_pred, columns=output_cols)

    # Insert tau (physical units) – taken from the average tau profile.
    # avg_tau_physical is stored in log10 space when log-transform is applied.
    if predictor.avg_tau_physical is not None:
        if predictor.stats and 'tau' in predictor.stats.get('log_transform_cols', []):
            tau_vals = 10 ** predictor.avg_tau_physical
        else:
            tau_vals = predictor.avg_tau_physical
    else:
        tau_vals = np.zeros(50, dtype=np.float32)
    df.insert(0, 'tau', tau_vals)


    # Save to file if requested
    filepath = None
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine filename extension
        ext = output_format.lower()
        if filename is None:
            filename = f"{teff}_{logg}_{mh}.{ext}"
        elif not filename.endswith(f'.{ext}'):
            filename = f"{filename}.{ext}"
        
        filepath = os.path.join(os.path.abspath(output_dir), filename)
        
        # Write in requested format
        if output_format.lower() == 'csv':


            # Insert stellar parameters (replicated for every depth row)
            df.insert(0, 'mh', float(mh))
            df.insert(0, 'logg', float(logg))
            df.insert(0, 'teff', float(teff))


            df.to_csv(filepath, index=False)
        elif output_format.lower() == '7':
            # Prepare model data dictionary for .7 format
            # n_params is number of columns excluding teff, logg, mh, tau
            model_data = {
                'dataframe': df,
                'n_depth': len(df),
                'n_params': 58
            }
            write_tlusty_model7(filepath, model_data)
        else:
            raise ValueError(f"Unsupported output_format: {output_format}. Use 'csv' or '7'")

    return df, filepath


class TlustyAtmosphere:
    """Convenient wrapper around :class:`TlustyPredictor`.

    Example
    -------
    >>> atm = TlustyAtmosphere()
    >>> df = atm.predict(10000, 3.7, 0.0)
    >>> df.to_csv('my_model.csv', index=False)
    """

    def __init__(self, checkpoint_path=None, device=None):
        self.predictor = TlustyPredictor(
            checkpoint_path=checkpoint_path, device=device
        )

    def predict(self, teff, logg, mh, output_dir=None, filename=None, 
                output_format='csv'):
        """Same interface as :func:`predict_atmosphere`."""
        result = self.predictor.predict(teff, logg, mh)
        y_pred = result['prediction'][0]

        if self.predictor.stats and 'output_cols' in self.predictor.stats:
            output_cols = self.predictor.stats['output_cols']
        else:
            output_cols = [f'col_{i}' for i in range(y_pred.shape[1])]

        df = pd.DataFrame(y_pred, columns=output_cols)

        if self.predictor.avg_tau_physical is not None:
            if self.predictor.stats and 'tau' in self.predictor.stats.get('log_transform_cols', []):
                tau_vals = 10 ** self.predictor.avg_tau_physical
            else:
                tau_vals = self.predictor.avg_tau_physical
        else:
            tau_vals = np.zeros(50, dtype=np.float32)
        df.insert(0, 'tau', tau_vals)


        filepath = None
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine filename extension
            ext = output_format.lower()
            if filename is None:
                filename = f"{teff}_{logg}_{mh}.{ext}"


            elif not filename.endswith(f'.{ext}'):
                filename = f"{filename}.{ext}"
            
            filepath = os.path.join(os.path.abspath(output_dir), filename)
            
            # Write in requested format
            if output_format.lower() == 'csv':

                df.insert(0, 'mh', float(mh))
                df.insert(0, 'logg', float(logg))
                df.insert(0, 'teff', float(teff))


                df.to_csv(filepath, index=False)


            elif output_format.lower() == '7':
                model_data = {
                    'dataframe': df,
                    'n_depth': len(df),
                    'n_params': 58
                }
                write_tlusty_model7(filepath, model_data)
            else:
                raise ValueError(f"Unsupported output_format: {output_format}. Use 'csv' or '7'")

        return df, filepath
    

    