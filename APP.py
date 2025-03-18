import time
import pandas as pd
import streamlit as st
from iqoptionapi.stable_api import IQ_Option  # pip install iqoptionapi
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

# === CONFIGURAÇÃO DA API ===
st.set_page_config(page_title="🤖 Robô IQ Option", layout="wide")

# Dados da API (armazene em variáveis de ambiente para segurança)
EMAIL = st.sidebar.text_input("Email da IQ Option", type="default")
PASSWORD = st.sidebar.text_input("Senha da IQ Option", type="password")
SYMBOL = st.sidebar.selectbox("Ativo", ["EURUSD", "GBPUSD", "BTCUSD"])
ACCOUNT_TYPE = st.sidebar.selectbox("Conta", ["PRACTICE", "REAL"])
INVESTMENT = st.sidebar.number_input("Valor por Operação ($)", min_value=10, value=10)
STOP_LOSS_PERCENT = st.sidebar.number_input("Stop-Loss (%)", min_value=1, max_value=100, value=10)

# Conectar à API
if EMAIL and PASSWORD:
    try:
        api = IQ_Option(EMAIL, PASSWORD)
        api.connect()
        if api.check_connect():
            st.sidebar.success("Conexão bem-sucedida!")
        else:
            st.sidebar.error("Erro na conexão. Verifique suas credenciais.")
    except Exception as e:
        st.sidebar.error(f"Erro na conexão: {e}")
else:
    st.sidebar.warning("Insira seu email e senha da IQ Option")

# === ANÁLISE TÉCNICA ===
def analyze_market(symbol, timeframe=60):
    """Obtém dados do mercado e calcula indicadores."""
    candles = api.get_candles(symbol, timeframe, 100, time.time())
    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)
    
    # Calcula SMA e RSI
    df['sma_short'] = SMAIndicator(close=df['close'], window=10).sma_indicator()
    df['sma_long'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    
    return df

# === MODO AUTOMÁTICO ===
def auto_mode():
    st.info("Modo automático ativado. Monitorando o mercado...")
    balance = api.get_balance()
    st.success(f"Saldo Atual: ${balance:.2f}")
    
    while True:
        df = analyze_market(SYMBOL)
        last_row = df.iloc[-1]
        
        # Verifica Stop-Loss
        current_balance = api.get_balance()
        if (balance - current_balance) / balance * 100 >= STOP_LOSS_PERCENT:
            st.error("Stop-Loss atingido! Parando operações.")
            break
        
        # Lógica de Trade
        if last_row['sma_short'] > last_row['sma_long'] and last_row['rsi'] < 30:
            st.balloons()
            st.success(f"Compra (Call) às {time.strftime('%H:%M:%S')}")
            api.buy(INVESTMENT, SYMBOL, "call", 1)
        elif last_row['sma_short'] < last_row['sma_long'] and last_row['rsi'] > 70:
            st.balloons()
            st.error(f"Venda (Put) às {time.strftime('%H:%M:%S')}")
            api.buy(INVESTMENT, SYMBOL, "put", 1)
        else:
            st.warning("Aguardando oportunidade...")
        
        time.sleep(60)  # Atualiza a cada minuto

# === MODO MANUAL ===
def manual_mode():
    st.info("Modo manual ativado. Analisando o gráfico...")
    df = analyze_market(SYMBOL)
    last_row = df.iloc[-1]
    
    # Exibir análise
    st.subheader("📊 Análise do Mercado")
    st.write(f"Último Preço: {last_row['close']:.5f}")
    st.write(f"SMA Curta (10): {last_row['sma_short']:.5f}")
    st.write(f"SMA Longa (50): {last_row['sma_long']:.5f}")
    st.write(f"RSI (14): {last_row['rsi']:.2f}")
    
    # Sinal de entrada
    if last_row['sma_short'] > last_row['sma_long'] and last_row['rsi'] < 30:
        st.success(f"Sinal de COMPRA (Call) detectado para {SYMBOL}!")
    elif last_row['sma_short'] < last_row['sma_long'] and last_row['rsi'] > 70:
        st.error(f"Sinal de VENDA (Put) detectado para {SYMBOL}!")
    else:
        st.warning("Nenhum sinal claro no momento.")

# === INTERFACE DO USUÁRIO ===
st.title("🚀 Robô de Opções Binárias (IQ Option)")
st.subheader("Configuração Simplificada")

# Escolher Modo
mode = st.radio("Escolha o Modo:", ("Modo Automático", "Modo Manual"))

if mode == "Modo Automático":
    if st.button("▶️ Iniciar Modo Automático"):
        auto_mode()
elif mode == "Modo Manual":
    if st.button("🔍 Analisar Gráfico"):
        manual_mode()

# Painel de Risco
st.subheader("风险管理")
st.progress(STOP_LOSS_PERCENT / 100)
st.caption(f"Stop-Loss configurado para {STOP_LOSS_PERCENT}%")

# Histórico de Trades
st.subheader(" Histórico de Operações")
trades = api.get_optioninfo(10)  # Últimas 10 operações
st.table(trades)
