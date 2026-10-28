import pandas as pd
import numpy as np
import os
import json

# ==========================================
# 1. FUNÇÕES AUXILIARES E DE EXTRAÇÃO
# ==========================================

def get_week(day):
    """Categoriza o dia do mês em 4 semanas para os relatórios."""
    if day <= 7: return 1
    elif day <= 14: return 2
    elif day <= 21: return 3
    else: return 4

def separar_arquivos_por_chave(file_path):
    """
    Filtra estritamente o mês/ano de interesse a partir do nome do arquivo
    e gera os 3 arquivos menores na pasta 'data/'.
    """
    file_name = os.path.basename(file_path)
    date_prefix = file_name.split("_")[0]
    yyyy = date_prefix[:4]
    mm = date_prefix[4:6]
    
    print(f"Lendo o arquivo principal... Referência: Mês {mm} / Ano {yyyy}")
    df = pd.read_csv(file_path, low_memory=False)
    
    print("Filtrando dados estritamente para o mês e ano do arquivo...")
    df['datetime_aux'] = pd.to_datetime(df['Time'], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
    df_mes = df[(df['datetime_aux'].dt.year == int(yyyy)) & (df['datetime_aux'].dt.month == int(mm))]
    df_mes = df_mes.drop(columns=['datetime_aux'])
    
    keys_to_extract = {
        'sleep': 'sleep',
        'steps': 'steps',
        'heart_rate': 'heart_rate'
    }
    
    os.makedirs("data", exist_ok=True)
    
    for key, prefix in keys_to_extract.items():
        df_filtered = df_mes[df_mes['Key'] == key]
        output_filepath = os.path.join("data", f"{prefix}_data_{mm}_{yyyy}.csv")
        df_filtered.to_csv(output_filepath, index=False)
        print(f"  -> Arquivo gerado: {output_filepath} | Total de registros: {len(df_filtered)}")
        
    print("\nSeparação e filtragem concluídas com sucesso!\n")
    print("=" * 60)
    
    return mm, yyyy


# ==========================================
# 2. MÓDULO DE PASSOS
# ==========================================

def calcular_score_passos(passos):
    if pd.isna(passos) or passos <= 0: return 0.0
    if passos >= 16000: return 100.0
    
    A = 51.70184
    B = 0.00036989
    return min(100.0, A * np.log(B * passos + 1))

def gerar_relatorio_passos(mm, yyyy):
    print("\n[ INICIANDO RELATÓRIO DE PASSOS ]\n")
    
    df_steps = pd.read_csv(os.path.join("data", f"steps_data_{mm}_{yyyy}.csv"), low_memory=False)
    
    parsed = df_steps['Value'].apply(lambda x: (json.loads(x).get('time'), json.loads(x).get('steps')) if pd.notna(x) else (None, None))
    df_steps['timestamp'] = [p[0] for p in parsed]
    df_steps['step_count'] = [p[1] for p in parsed]
    df_steps = df_steps.dropna(subset=['timestamp', 'step_count'])
    
    df_steps['datetime'] = pd.to_datetime(df_steps['timestamp'], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
    df_steps['date'] = df_steps['datetime'].dt.date
    
    daily_steps = df_steps.groupby('date')['step_count'].sum().reset_index()
    daily_steps['score'] = daily_steps['step_count'].apply(calcular_score_passos)
    daily_steps['day_number'] = pd.to_datetime(daily_steps['date']).dt.day
    daily_steps['week'] = daily_steps['day_number'].apply(get_week)
    
    total_month = daily_steps['step_count'].sum()
    avg_month = daily_steps['step_count'].mean()
    avg_score_month = daily_steps['score'].mean()
    
    weekly_totals = daily_steps.groupby('week')['step_count'].sum()
    weekly_avgs = daily_steps.groupby('week')['step_count'].mean()
    weekly_scores = daily_steps.groupby('week')['score'].mean()
    
    print(f"--- RESULTADOS PASSOS: {mm}/{yyyy} ---")
    print(f"Total de passos no mês: {total_month:,.0f}".replace(",", "."))
    print(f"Média de passos por dia: {avg_month:,.0f}".replace(",", "."))
    print(f"SCORE MENSAL MÉDIO: {avg_score_month:.1f} / 100")
    print("\nDesempenho por Semana (Passos):")
    
    for week in range(1, 5):
        if week in weekly_totals.index:
            labels = ["Dias 01 a 07", "Dias 08 a 14", "Dias 15 a 21", "Dia 22 ao fim"]
            print(f"  Semana {week} ({labels[week-1]}):")
            print(f"    - Passos Totais: {weekly_totals[week]:,.0f}".replace(",", "."))
            print(f"    - Média Diária:  {weekly_avgs[week]:,.0f}".replace(",", "."))
            print(f"    - Score da Sem:  {weekly_scores[week]:.1f} / 100")
    print("=" * 60)
    
    return daily_steps


# ==========================================
# 3. MÓDULO DE SONO
# ==========================================

def calcular_score_sono(value_json_str):
    try: data = json.loads(value_json_str)
    except: return 0.0
        
    T = data.get('duration', 0)
    if T == 0: return 0.0

    Deep, REM = data.get('sleep_deep_duration', 0), data.get('sleep_rem_duration', 0)
    Wake, Breath = data.get('sleep_awake_duration', 0), data.get('breath_quality', 0)

    if T < 240: score_tst = 0
    elif T < 420: score_tst = 30 * ((T - 240) / 180)
    elif T <= 540: score_tst = 30
    else: score_tst = max(0, 30 - ((T - 540) / 15))

    score_deep = 20 if (Deep / T) >= 0.15 else 20 * ((Deep / T) / 0.15)
    score_rem = 20 if (REM / T) >= 0.20 else 20 * ((REM / T) / 0.20)

    efficiency = T / (T + Wake) if (T + Wake) > 0 else 0
    score_se = 15 if efficiency >= 0.85 else max(0, 15 * ((efficiency - 0.50) / 0.35))

    score_cont = 10 if Wake <= 20 else max(0, 10 - ((Wake - 20) / 5))
    score_breath = 5 if Breath >= 95 else max(0, 5 * ((Breath - 70) / 25))

    return round(score_tst + score_deep + score_rem + score_se + score_cont + score_breath, 2)

def gerar_relatorio_sono(mm, yyyy):
    print("\n[ INICIANDO RELATÓRIO DE SONO ]\n")
    
    df_sleep = pd.read_csv(os.path.join("data", f"sleep_data_{mm}_{yyyy}.csv"), low_memory=False)
    
    parsed = df_sleep['Value'].apply(lambda x: (json.loads(x).get('wake_up_time'), json.loads(x).get('duration')) if pd.notna(x) else (None, None))
    df_sleep['timestamp'] = [p[0] for p in parsed]
    df_sleep['duration_mins'] = [p[1] for p in parsed]
    df_sleep = df_sleep.dropna(subset=['timestamp', 'duration_mins'])
    
    df_sleep['score'] = df_sleep['Value'].apply(calcular_score_sono)
    df_sleep['datetime'] = pd.to_datetime(df_sleep['timestamp'], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
    df_sleep['date'] = df_sleep['datetime'].dt.date
    
    daily_sleep = df_sleep.groupby('date').agg({'duration_mins': 'sum', 'score': 'mean'}).reset_index()
    daily_sleep['duration_hours'] = daily_sleep['duration_mins'] / 60
    daily_sleep['day_number'] = pd.to_datetime(daily_sleep['date']).dt.day
    daily_sleep['week'] = daily_sleep['day_number'].apply(get_week)
    
    print(f"--- RESULTADOS SONO: {mm}/{yyyy} ---")
    print(f"Média de duração no mês: {daily_sleep['duration_hours'].mean():.1f} hrs/noite")
    print(f"SCORE MENSAL MÉDIO: {daily_sleep['score'].mean():.1f} / 100")
    print("\nDesempenho por Semana (Sono):")
    
    weekly_avg_h = daily_sleep.groupby('week')['duration_hours'].mean()
    weekly_scores = daily_sleep.groupby('week')['score'].mean()
    
    for week in range(1, 5):
        if week in weekly_scores.index:
            labels = ["Dias 01 a 07", "Dias 08 a 14", "Dias 15 a 21", "Dia 22 ao fim"]
            print(f"  Semana {week} ({labels[week-1]}):")
            print(f"    - Duração Média: {weekly_avg_h[week]:.1f} hrs/noite")
            print(f"    - Score da Sem:  {weekly_scores[week]:.1f} / 100")
    print("=" * 60)
    
    return daily_sleep


# ==========================================
# 4. MÓDULO DE CORAÇÃO
# ==========================================

def calcular_score_cardiaco_diario(bpm_series):
    bpm = bpm_series.dropna()
    if len(bpm) == 0:
        return 0.0
        
    p5 = np.percentile(bpm, 5)
    sd = np.std(bpm)
    recovery_pct = (bpm <= 75).mean()
    m = np.max(bpm)
    
    if 45 <= p5 <= 65: s1 = 35
    elif p5 > 65: s1 = max(0, 35 - ((p5 - 65) / 20) * 35)
    else: s1 = max(0, 35 - ((45 - p5) / 10) * 35)
        
    if sd >= 15: s2 = 25
    else: s2 = max(0, 25 * ((sd - 5) / 10))
        
    if recovery_pct >= 0.55: s3 = 20
    else: s3 = max(0, 20 * ((recovery_pct - 0.20) / 0.35))
        
    if m >= 115: s4 = 20
    else: s4 = max(0, 20 * ((m - 90) / 25))
        
    return round(s1 + s2 + s3 + s4, 2)

def gerar_relatorio_cardiaco(mm, yyyy):
    print("\n[ INICIANDO RELATÓRIO CARDÍACO ]\n")
    
    df_hr = pd.read_csv(os.path.join("data", f"heart_rate_data_{mm}_{yyyy}.csv"), low_memory=False)
    
    def parse_hr(val):
        try:
            d = json.loads(val)
            return d.get('time'), d.get('bpm')
        except:
            return None, None
            
    parsed = df_hr['Value'].apply(parse_hr)
    df_hr['timestamp'] = [p[0] for p in parsed]
    df_hr['bpm'] = [p[1] for p in parsed]
    
    df_hr = df_hr.dropna(subset=['timestamp', 'bpm'])
    df_hr['datetime'] = pd.to_datetime(df_hr['timestamp'], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
    df_hr['date'] = df_hr['datetime'].dt.date
    
    daily_hr = df_hr.groupby('date')['bpm'].apply(calcular_score_cardiaco_diario).reset_index()
    daily_hr = daily_hr.rename(columns={'bpm': 'score'})
    
    daily_hr['day_number'] = pd.to_datetime(daily_hr['date']).dt.day
    daily_hr['week'] = daily_hr['day_number'].apply(get_week)
    
    print(f"--- RESULTADOS CARDÍACOS: {mm}/{yyyy} ---")
    print(f"SCORE MENSAL MÉDIO: {daily_hr['score'].mean():.1f} / 100")
    print("\nDesempenho por Semana (Cardíaco):")
    
    weekly_scores = daily_hr.groupby('week')['score'].mean()
    
    for week in range(1, 5):
        if week in weekly_scores.index:
            labels = ["Dias 01 a 07", "Dias 08 a 14", "Dias 15 a 21", "Dia 22 ao fim"]
            print(f"  Semana {week} ({labels[week-1]}):")
            print(f"    - Score da Sem:  {weekly_scores[week]:.1f} / 100")
    print("=" * 60)
    
    return daily_hr


# ==========================================
# 5. MÓDULO DE CONSOLIDAÇÃO GERAL
# ==========================================

def calcular_score_global(df_steps, df_sleep, df_hr):
    print("\n[ INICIANDO RELATÓRIO GLOBAL DE SAÚDE ]\n")
    
    # Prepara e renomeia as colunas de score para evitar conflitos no merge
    df1 = df_steps[['date', 'score']].rename(columns={'score': 'score_passos'})
    df2 = df_sleep[['date', 'score']].rename(columns={'score': 'score_sono'})
    df3 = df_hr[['date', 'score']].rename(columns={'score': 'score_cardiaco'})
    
    # Mescla os dataframes utilizando a data como chave principal
    df_merged = pd.merge(df1, df2, on='date', how='outer')
    df_merged = pd.merge(df_merged, df3, on='date', how='outer')
    
    # Preenche dias com ausência de leitura do relógio com 0
    df_merged = df_merged.fillna(0)
    
    # Aplica a fórmula com os pesos da literatura esportiva
    peso_sono = 0.45
    peso_cardiaco = 0.35
    peso_passos = 0.20
    
    df_merged['score_geral'] = (
        (df_merged['score_sono'] * peso_sono) + 
        (df_merged['score_cardiaco'] * peso_cardiaco) + 
        (df_merged['score_passos'] * peso_passos)
    )
    
    # Garante que as datas existam adequadamente para o cálculo das semanas
    df_merged['day_number'] = pd.to_datetime(df_merged['date']).dt.day
    df_merged['week'] = df_merged['day_number'].apply(get_week)
    
    # Exibe os resultados consolidados
    print(f"--- RESULTADO GLOBAL INTEGRADO ---")
    print(f"SCORE GERAL MENSAL MÉDIO: {df_merged['score_geral'].mean():.1f} / 100\n")
    
    weekly_scores = df_merged.groupby('week')['score_geral'].mean()
    
    for week in range(1, 5):
        if week in weekly_scores.index:
            labels = ["Dias 01 a 07", "Dias 08 a 14", "Dias 15 a 21", "Dia 22 ao fim"]
            print(f"  Semana {week} ({labels[week-1]}): {weekly_scores[week]:.1f} / 100")
            
    print("=" * 60)
    return df_merged


# ==========================================
# 6. EXECUÇÃO PRINCIPAL
# ==========================================

if __name__ == "__main__":
    caminho_arquivo_original = "data/20260929_6289526178_MiFitness_hlth_center_fitness_data.csv"
    
    mes, ano = separar_arquivos_por_chave(caminho_arquivo_original)
    
    df_passos = gerar_relatorio_passos(mes, ano)
    df_sono = gerar_relatorio_sono(mes, ano)
    df_cardiaco = gerar_relatorio_cardiaco(mes, ano)
    
    # Gera o score final cruzando todas as métricas
    df_consolidado = calcular_score_global(df_passos, df_sono, df_cardiaco)
    
    print("\nProcessamento completo de todos os relatórios concluído!\n")
