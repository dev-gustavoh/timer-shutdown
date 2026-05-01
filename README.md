# ⏱ Timer Shutdown

Aplicativo Windows para agendar desligamento, reinicialização ou suspensão do computador.

---

## Requisitos

- **Python 3.8+** instalado ([python.org](https://www.python.org/downloads/))
- Nenhuma dependência externa — usa apenas a biblioteca padrão do Python (`tkinter`)

---

## Como rodar

```bash
python timer_shutdown.py
```

> Se o Windows tiver múltiplas versões de Python, use `python3 timer_shutdown.py` ou o caminho completo do executável.

---

## Funcionalidades

| Recurso | Descrição |
|---|---|
| **Horas / Minutos / Segundos** | Defina o tempo com precisão |
| **Desligar / Reiniciar / Suspender** | Escolha a ação desejada |
| **Contagem regressiva** | Display digital em tempo real |
| **Barra de progresso** | Visualização do tempo restante |
| **Aviso automático** | Pop-up 60 segundos antes da ação |
| **Últimos 10 segundos** | Contador muda para vermelho |
| **Botão Cancelar** | Interrompe o timer a qualquer momento |

---

## Como gerar o executável (.exe)

### 1. Instale o PyInstaller

```bash
pip install pyinstaller
```

### 2. Gere o executável

```bash
pyinstaller --onefile --windowed --name "TimerShutdown" timer_shutdown.py
```

| Flag | Descrição |
|---|---|
| `--onefile` | Gera um único arquivo `.exe` |
| `--windowed` | Oculta o console (modo GUI) |
| `--name "TimerShutdown"` | Nome do executável gerado |

### 3. Localize o executável

Após a compilação, o `.exe` estará em:

```
dist/TimerShutdown.exe
```

Execute direto — não precisa de Python instalado na máquina de destino.

---

## Observações

- O botão **Cancelar** também executa `shutdown /a` no Windows, cancelando qualquer desligamento agendado.
- A ação de **Suspender** usa `rundll32.exe powrprof.dll,SetSuspendState` — funciona na maioria das configurações do Windows.
- O desligamento e reinicialização têm um atraso de **10 segundos** após o fim do timer, o que permite fechar outros programas.
