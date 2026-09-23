<!doctype html>
<html lang="${locale}">
  <head>
    <meta charset="utf-8">
    <base href="${resourceUrl}/">
    <link rel="icon" type="${properties.favIconType!'image/svg+xml'}" href="${resourceUrl}${properties.favIcon!'/favicon.svg'}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light${darkMode?then(' dark', '')}">
    <meta name="description" content="${properties.description!'The V-App Account Console is a web-based interface for managing your account.'}">
    <title>${properties.title!'V-App Account Management'}</title>
    <style>
      body {
        margin: 0;
      }

      body, #app {
        height: 100%;
      }

      .container {
        padding: 0;
        margin: 0;
        width: 100%;
      }

      .keycloak__loading-container {
        height: 100vh;
        width: 100%;
        color: #151515;
        background-color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        margin: 0;
      }

      @media (prefers-color-scheme: dark) {
        .keycloak__loading-container {
          color: #e0e0e0;
          background-color: #1b1d21;
        }
      }

      #loading-text {
        z-index: 1000;
        font-size: 20px;
        font-weight: 600;
        padding-top: 32px;
      }
    </style>
    <script type="importmap">
      {
        "imports": {
          "react": "${resourceCommonUrl}/vendor/react/react.production.min.js",
          "react/jsx-runtime": "${resourceCommonUrl}/vendor/react/react-jsx-runtime.production.min.js",
          "react-dom": "${resourceCommonUrl}/vendor/react-dom/react-dom.production.min.js"
        }
      }
    </script>
    <#if darkMode>
      <script type="module" async blocking="render">
          const DARK_MODE_CLASS = "${properties.kcDarkModeClass}";
          const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

          updateDarkMode(mediaQuery.matches);
          mediaQuery.addEventListener("change", (event) => updateDarkMode(event.matches));

          function updateDarkMode(isEnabled) {
            const { classList } = document.documentElement;

            if (isEnabled) {
              classList.add(DARK_MODE_CLASS);
            } else {
              classList.remove(DARK_MODE_CLASS);
            }
          }
      </script>
    </#if>
    <#if !isSecureContext>
      <script type="module" src="${resourceCommonUrl}/vendor/web-crypto-shim/web-crypto-shim.js"></script>
    </#if>
    <#if devServerUrl?has_content>
      <script type="module">
        import { injectIntoGlobalHook } from "${devServerUrl}/@react-refresh";

        injectIntoGlobalHook(window);
        window.$RefreshReg$ = () => {};
        window.$RefreshSig$ = () => (type) => type;
      </script>
      <script type="module">
        import { inject } from "${devServerUrl}/@vite-plugin-checker-runtime";

        inject({
          overlayConfig: {},
          base: "/",
        });
      </script>
      <script type="module" src="${devServerUrl}/@vite/client"></script>
      <script type="module" src="${devServerUrl}/src/main.tsx"></script>
    </#if>
    <#if entryStyles?has_content>
      <#list entryStyles as style>
        <link rel="stylesheet" href="${resourceUrl}/${style}">
      </#list>
    </#if>
    <#if properties.styles?has_content>
      <#list properties.styles?split(' ') as style>
        <link rel="stylesheet" href="${resourceUrl}/${style}">
      </#list>
    </#if>
    <#if entryScript?has_content>
      <script type="module" src="${resourceUrl}/${entryScript}"></script>
    </#if>
    <#if properties.scripts?has_content>
      <#list properties.scripts?split(' ') as script>
        <script type="module" src="${resourceUrl}/${script}"></script>
      </#list>
    </#if>
    <#if entryImports?has_content>
      <#list entryImports as import>
        <link rel="modulepreload" href="${resourceUrl}/${import}">
      </#list>
    </#if>
  </head>
  <body data-page-id="account">
    <div id="app">
      <main class="container">
        <div class="keycloak__loading-container">
          <svg class="pf-v5-c-spinner pf-m-xl" role="progressbar" aria-valuetext="Loading..." viewBox="0 0 100 100" aria-label="Contents">
            <circle class="pf-v5-c-spinner__path" cx="50" cy="50" r="45" fill="none"></circle>
          </svg>
          <div>
            <p id="loading-text">Loading V-App Account Console</p>
          </div>
        </div>
      </main>
    </div>
    <noscript>JavaScript is required to use the V-App Account Console.</noscript>
    <script id="environment" type="application/json">
      {
        "serverBaseUrl": "${serverBaseUrl}",
        "authUrl": "${authUrl}",
        "authServerUrl": "${authServerUrl}",
        "realm": "${realm.name}",
        "clientId": "${clientId}",
        "resourceUrl": "${resourceUrl}",
        "logo": "${properties.logo!""}",
        "logoUrl": "${properties.logoUrl!""}",
        "baseUrl": "${baseUrl}",
        "locale": "${locale}",
        "referrerName": "${referrerName!""}",
        "referrerUrl": "${referrer_uri!""}",
        "features": {
          "isRegistrationEmailAsUsername": ${(realm.registrationEmailAsUsername!false)?c},
          "isEditUserNameAllowed": ${(realm.editUsernameAllowed!false)?c},
          "isInternationalizationEnabled": ${(realm.isInternationalizationEnabled()!false)?c},
          "isLinkedAccountsEnabled": ${(realm.identityFederationEnabled!false)?c},
          "isMyResourcesEnabled": ${((realm.userManagedAccessAllowed!false) && (isAuthorizationEnabled!false))?c},
          "isViewOrganizationsEnabled": ${(isViewOrganizationsEnabled!false)?c},
          "deleteAccountAllowed": ${(deleteAccountAllowed!false)?c},
          "updateEmailFeatureEnabled": ${(updateEmailFeatureEnabled!false)?c},
          "updateEmailActionEnabled": ${(updateEmailActionEnabled!false)?c},
          "isViewGroupsEnabled": ${(isViewGroupsEnabled!false)?c},
          "isOid4VciEnabled": ${(isOid4VciEnabled!false)?c}
        },
        "scope": "${scope!""}"
      }
    </script>
    <script>
      // V-App Branding: Replace Keycloak references in account UI
      (function() {
        function replaceKeycloakText() {
          var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
          while (walker.nextNode()) {
            var node = walker.currentNode;
            if (node.nodeValue && /keycloak/i.test(node.nodeValue)) {
              node.nodeValue = node.nodeValue
                .replace(/Keycloak\s+Account\s+Management/gi, 'V-App Account Management')
                .replace(/Keycloak/gi, 'V-App');
            }
          }
          if (document.title && /keycloak/i.test(document.title)) {
            document.title = document.title.replace(/Keycloak/gi, 'V-App');
          }
        }

        var attempts = 0;
        var interval = setInterval(function() {
          replaceKeycloakText();
          attempts++;
          if (attempts > 50) clearInterval(interval);
        }, 500);

        var observer = new MutationObserver(function() {
          replaceKeycloakText();
        });

        if (document.body) {
          observer.observe(document.body, { childList: true, subtree: true });
        } else {
          document.addEventListener('DOMContentLoaded', function() {
            observer.observe(document.body, { childList: true, subtree: true });
            replaceKeycloakText();
          });
        }
      })();
    </script>
  </body>
</html>
