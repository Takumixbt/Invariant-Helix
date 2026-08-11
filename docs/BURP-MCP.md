# Load Burp MCP on Windows (step-by-step)

You already have Burp installed. The MCP jar is built at:

```text
C:\Users\Takum\tools\Burp-MCP-Unrestricted\build\libs\burp-mcp-all.jar
```

## Steps

1. **Start Burp**  
   `C:\Users\Takum\AppData\Local\Programs\BurpSuite\BurpSuite.exe`  
   (or Start Menu → Burp Suite)

2. Create/open a **temporary project** (Community is fine).

3. Open **Extensions**  
   - Top menu: **Extensions** → **Installed**  
   - Or: **Extender** → **Extensions** (older UI)

4. Click **Add**

5. In the dialog:
   - **Extension type:** `Java`
   - **Extension file (.jar):** browse to  
     `C:\Users\Takum\tools\Burp-MCP-Unrestricted\build\libs\burp-mcp-all.jar`
   - Leave other fields default
   - Click **Next** → **Close**

6. Check the **Output** / **Errors** tab for the extension  
   - Success: no stack traces; MCP / proxy server notes appear  
   - Failure: wrong Java, corrupt jar, or path with bad permissions — rebuild:
     ```powershell
     cd $HOME\tools\Burp-MCP-Unrestricted
     $env:JAVA_HOME = "$HOME\tools\jdk-21"
     $env:Path = "$env:JAVA_HOME\bin;$env:Path"
     .\gradlew.bat embedProxyJar --no-daemon
     ```

7. **Re-enable approval prompts** if this unrestricted fork disabled them  
   (see extension options / README for the fork). Do not leave unrestricted auto-approve on shared machines.

8. Point your agent MCP config at the Burp MCP endpoint the extension prints  
   (host/port from extension output — often localhost).

## Verify without MCP

IH already has proxy capability via **mitmdump**:

```powershell
mitmdump --version
ih-check-capabilities
```

Burp is optional polish for interactive proxy + agent control.
