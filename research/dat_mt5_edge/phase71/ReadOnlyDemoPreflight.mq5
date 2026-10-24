#property strict
#property script_show_inputs
#property version "1.00"
// PREPARATION ONLY. No terminal/account startup, imports, order effects or fallback.
// Run only after separate Gate A approval in an isolated investor/read-only login.
input bool GateAApproved=false;
input string ApprovalReference="";
input string SessionNonce="";
input datetime ApprovedFromUTC=0;
input datetime ApprovedUntilUTC=0;
input bool InvestorAccessIndependentlyVerified=false;
input bool IsolationIndependentlyVerified=false;
input long ExpectedLogin=0;
input string ExpectedServer="";
input string ExpectedCompany="";
input string ExpectedCurrency="";
input string ExpectedTerminalName="";
input string ExpectedTerminalPath="";
input string ExpectedDataPath="";
input int ExpectedBuild=0;
input string EURUSDSymbol="";
input string GBPUSDSymbol="";
input string XAUUSDSymbol="";
input string BTCUSDSymbol="";

ulong Started=0;

string J(string value)
{
   StringReplace(value,"\\","\\\\"); StringReplace(value,"\"","\\\"");
   StringReplace(value,"\r","\\r"); StringReplace(value,"\n","\\n"); StringReplace(value,"\t","\\t");
   return "\""+value+"\"";
}
string B(bool value) { return value ? "true" : "false"; }
bool Label(string value)
{
   if(StringLen(value)<1 || StringLen(value)>64) return false;
   string alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
   for(int i=0;i<StringLen(value);i++)
      if(StringFind(alphabet,StringSubstr(value,i,1))<0) return false;
   return true;
}
bool Pinned()
{
   ResetLastError();
   if(IsStopped()) return false;
   datetime now=TimeGMT();
   if(!GateAApproved || !InvestorAccessIndependentlyVerified || !IsolationIndependentlyVerified) return false;
   if(!Label(ApprovalReference) || !Label(SessionNonce) || ExpectedLogin<=0 || ExpectedBuild<=0) return false;
   if(ExpectedServer!="VantageMarkets-Demo" || ExpectedCompany=="" || ExpectedCurrency=="" || ExpectedTerminalName=="") return false;
   if(ExpectedTerminalPath=="" || ExpectedDataPath=="" || ExpectedTerminalPath==ExpectedDataPath) return false;
   if(ApprovedFromUTC<=0 || ApprovedUntilUTC<=ApprovedFromUTC || ApprovedUntilUTC-ApprovedFromUTC>600) return false;
   if(now<ApprovedFromUTC || now>=ApprovedUntilUTC || GetMicrosecondCount()-Started>5000000) return false;
   if(AccountInfoInteger(ACCOUNT_LOGIN)!=ExpectedLogin || AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   if(AccountInfoString(ACCOUNT_SERVER)!=ExpectedServer || AccountInfoString(ACCOUNT_COMPANY)!=ExpectedCompany) return false;
   if(AccountInfoString(ACCOUNT_CURRENCY)!=ExpectedCurrency || AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
   if(!TerminalInfoInteger(TERMINAL_CONNECTED) || TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(TerminalInfoInteger(TERMINAL_DLLS_ALLOWED) || MQLInfoInteger(MQL_DLLS_ALLOWED) || MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
   if(TerminalInfoInteger(TERMINAL_BUILD)!=ExpectedBuild || TerminalInfoString(TERMINAL_NAME)!=ExpectedTerminalName) return false;
   if(TerminalInfoString(TERMINAL_PATH)!=ExpectedTerminalPath || TerminalInfoString(TERMINAL_DATA_PATH)!=ExpectedDataPath) return false;
   if(PositionsTotal()!=0 || OrdersTotal()!=0) return false;
   return GetLastError()==0;
}
string DI(string symbol,ENUM_SYMBOL_INFO_DOUBLE property,bool &ok)
{
   double v=0;
   if(!SymbolInfoDouble(symbol,property,v) || !MathIsValidNumber(v)) ok=false;
   return J(DoubleToString(v,16));
}
string II(string symbol,ENUM_SYMBOL_INFO_INTEGER property,bool &ok)
{
   long v=0; if(!SymbolInfoInteger(symbol,property,v)) ok=false;
   return IntegerToString(v);
}
string SI(string symbol,ENUM_SYMBOL_INFO_STRING property,bool &ok)
{
   string v=""; if(!SymbolInfoString(symbol,property,v)) ok=false;
   return J(v);
}
bool SymbolSnapshot(string alias,string symbol,string &out)
{
   if(!Pinned() || symbol=="" || StringLen(symbol)>96) return false;
   bool ok=true;
   if(!SymbolInfoInteger(symbol,SYMBOL_EXIST) || !SymbolInfoInteger(symbol,SYMBOL_SELECT) || SymbolInfoInteger(symbol,SYMBOL_CUSTOM)) return false;
   MqlTick tick;
   if(!SymbolInfoTick(symbol,tick) || !MathIsValidNumber(tick.bid) || !MathIsValidNumber(tick.ask) || tick.time_msc<=0 || tick.bid<=0 || tick.ask<tick.bid) return false;
   long age=(long)TimeTradeServer()*1000-tick.time_msc;
   if(age < -1000 || age>5000) return false;
   if(age<0) age=0; // server clock is reported to whole seconds
   double volume=SymbolInfoDouble(symbol,SYMBOL_VOLUME_MIN), buy_margin=0,sell_margin=0;
   // Calculation only: no trade request/check/send is created or submitted.
   if(volume<=0 || !OrderCalcMargin(ORDER_TYPE_BUY,symbol,volume,tick.ask,buy_margin)) return false;
   if(!OrderCalcMargin(ORDER_TYPE_SELL,symbol,volume,tick.bid,sell_margin)) return false;
   if(!MathIsValidNumber(buy_margin) || !MathIsValidNumber(sell_margin) || buy_margin<=0 || sell_margin<=0) return false;
   int digits=(int)SymbolInfoInteger(symbol,SYMBOL_DIGITS);
   if(digits<0 || digits>10) return false;
   out="{\"alias\":"+J(alias)+",\"broker_symbol\":"+J(symbol)+",\"exists\":true,\"selected\":true,\"custom\":false";
   out+=",\"calc_mode\":"+II(symbol,SYMBOL_TRADE_CALC_MODE,ok);
   out+=",\"trade_mode\":"+II(symbol,SYMBOL_TRADE_MODE,ok);
   out+=",\"execution_mode\":"+II(symbol,SYMBOL_TRADE_EXEMODE,ok);
   out+=",\"filling_mode\":"+II(symbol,SYMBOL_FILLING_MODE,ok);
   out+=",\"digits\":"+II(symbol,SYMBOL_DIGITS,ok);
   out+=",\"stops_level_points\":"+II(symbol,SYMBOL_TRADE_STOPS_LEVEL,ok);
   out+=",\"freeze_level_points\":"+II(symbol,SYMBOL_TRADE_FREEZE_LEVEL,ok);
   out+=",\"point\":"+DI(symbol,SYMBOL_POINT,ok);
   out+=",\"contract_size\":"+DI(symbol,SYMBOL_TRADE_CONTRACT_SIZE,ok);
   out+=",\"tick_size\":"+DI(symbol,SYMBOL_TRADE_TICK_SIZE,ok);
   out+=",\"tick_value\":"+DI(symbol,SYMBOL_TRADE_TICK_VALUE,ok);
   out+=",\"tick_value_profit\":"+DI(symbol,SYMBOL_TRADE_TICK_VALUE_PROFIT,ok);
   out+=",\"tick_value_loss\":"+DI(symbol,SYMBOL_TRADE_TICK_VALUE_LOSS,ok);
   out+=",\"volume_min\":"+DI(symbol,SYMBOL_VOLUME_MIN,ok);
   out+=",\"volume_max\":"+DI(symbol,SYMBOL_VOLUME_MAX,ok);
   out+=",\"volume_step\":"+DI(symbol,SYMBOL_VOLUME_STEP,ok);
   out+=",\"volume_limit\":"+DI(symbol,SYMBOL_VOLUME_LIMIT,ok);
   out+=",\"margin_initial\":"+DI(symbol,SYMBOL_MARGIN_INITIAL,ok);
   out+=",\"margin_maintenance\":"+DI(symbol,SYMBOL_MARGIN_MAINTENANCE,ok);
   out+=",\"currency_profit\":"+SI(symbol,SYMBOL_CURRENCY_PROFIT,ok);
   out+=",\"currency_margin\":"+SI(symbol,SYMBOL_CURRENCY_MARGIN,ok);
   out+=",\"margin_buy_minlot\":"+J(DoubleToString(buy_margin,16));
   out+=",\"margin_sell_minlot\":"+J(DoubleToString(sell_margin,16));
   out+=",\"quote\":{\"bid\":"+J(DoubleToString(tick.bid,digits))+",\"ask\":"+J(DoubleToString(tick.ask,digits));
   out+=",\"time_msc\":"+IntegerToString(tick.time_msc)+",\"age_ms\":"+IntegerToString(age)+",\"age_basis\":\"SERVER_RELATIVE_ESTIMATE\"}}";
   return ok && Pinned();
}
void OnStart()
{
   Started=GetMicrosecondCount();
   if(!Pinned()) { Print("DAT_GATE_A_NO_GO: ADMISSION"); return; }
   string symbols[4]={EURUSDSymbol,GBPUSDSymbol,XAUUSDSymbol,BTCUSDSymbol};
   string aliases[4]={"EURUSD","GBPUSD","XAUUSD","BTCUSD"};
   for(int i=0;i<4;i++)
      for(int j=0;j<i;j++)
         if(symbols[i]==symbols[j]) { Print("DAT_GATE_A_NO_GO: MAPPING"); return; }
   string filename="DAT_GATE_A_"+SessionNonce+".json";
   if(FileIsExist(filename)) { Print("DAT_GATE_A_NO_GO: OUTPUT_EXISTS"); return; }
   ResetLastError();
   long captured=(long)TimeGMT()*1000;
   string payload="{\"schema\":\"DAT_MT5_READONLY_PREFLIGHT_V1\",\"approval_reference\":"+J(ApprovalReference)+",\"session_nonce\":"+J(SessionNonce);
   payload+=",\"captured_utc_ms\":"+IntegerToString(captured);
   payload+=",\"private_identity\":{\"login\":"+IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   payload+=",\"server\":"+J(AccountInfoString(ACCOUNT_SERVER))+",\"company\":"+J(AccountInfoString(ACCOUNT_COMPANY));
   payload+=",\"currency\":"+J(AccountInfoString(ACCOUNT_CURRENCY))+",\"trade_mode\":"+IntegerToString(AccountInfoInteger(ACCOUNT_TRADE_MODE));
   payload+=",\"trade_allowed\":"+B((bool)AccountInfoInteger(ACCOUNT_TRADE_ALLOWED));
   payload+=",\"expert_trade_allowed\":"+B((bool)AccountInfoInteger(ACCOUNT_TRADE_EXPERT));
   payload+=",\"leverage\":"+IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE));
   payload+=",\"margin_mode\":"+IntegerToString(AccountInfoInteger(ACCOUNT_MARGIN_MODE));
   payload+=",\"positions\":"+IntegerToString(PositionsTotal())+",\"orders\":"+IntegerToString(OrdersTotal())+"}";
   payload+=",\"terminal\":{\"name\":"+J(TerminalInfoString(TERMINAL_NAME))+",\"build\":"+IntegerToString(TerminalInfoInteger(TERMINAL_BUILD));
   payload+=",\"path\":"+J(TerminalInfoString(TERMINAL_PATH))+",\"data_path\":"+J(TerminalInfoString(TERMINAL_DATA_PATH));
   payload+=",\"connected\":"+B((bool)TerminalInfoInteger(TERMINAL_CONNECTED));
   payload+=",\"trade_allowed\":"+B((bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED));
   payload+=",\"dlls_allowed\":"+B((bool)TerminalInfoInteger(TERMINAL_DLLS_ALLOWED));
   payload+=",\"script_trade_allowed\":"+B((bool)MQLInfoInteger(MQL_TRADE_ALLOWED));
   payload+=",\"script_dlls_allowed\":"+B((bool)MQLInfoInteger(MQL_DLLS_ALLOWED));
   payload+=",\"ping_us\":"+IntegerToString(TerminalInfoInteger(TERMINAL_PING_LAST))+"}";
   payload+=",\"available_symbol_count\":"+IntegerToString(SymbolsTotal(false))+",\"symbols\":[";
   if(GetLastError()!=0) { Print("DAT_GATE_A_NO_GO: METADATA_READ"); return; }
   for(int i=0;i<4;i++)
   {
      string spec="";
      if(!SymbolSnapshot(aliases[i],symbols[i],spec)) { Print("DAT_GATE_A_NO_GO: SYMBOL_OR_FENCE"); return; }
      if(i>0) payload+=",";
      payload+=spec;
   }
   payload+="],\"duration_us\":"+IntegerToString((long)(GetMicrosecondCount()-Started))+",\"final_fence_ok\":"+B(Pinned())+"}";
   if(!Pinned() || StringLen(payload)>16000) { Print("DAT_GATE_A_NO_GO: FINAL_FENCE_OR_SIZE"); return; }
   int file=FileOpen(filename,FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(file==INVALID_HANDLE) { Print("DAT_GATE_A_NO_GO: OUTPUT"); return; }
   uchar encoded[]; int expected=StringToCharArray(payload,encoded,0,WHOLE_ARRAY,CP_UTF8)-1;
   uint written=FileWriteString(file,payload); ulong size=FileSize(file); FileClose(file);
   if(written!=(uint)expected || size!=(ulong)expected) { Print("DAT_GATE_A_NO_GO: WRITE"); return; }
   Print("DAT_GATE_A_CAPTURE_COMPLETE: PRIVATE_SNAPSHOT_REQUIRES_OFFLINE_VALIDATION");
}
