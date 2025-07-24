import * as React from 'react';
import PropTypes from 'prop-types';
import { ThemeProvider, createTheme, useColorScheme } from '@mui/material/styles';

import { inputsCustomizations } from './customizations/inputs';
import { dataDisplayCustomizations } from './customizations/dataDisplay';
import { feedbackCustomizations } from './customizations/feedback';
import { navigationCustomizations } from './customizations/navigation';
import { surfacesCustomizations } from './customizations/surfaces';
import { colorSchemes, typography, shadows, shape, forceDarkModeCSS, forceSystemModeToDark } from './themePrimitives.jsx';

// Style element to inject force dark mode CSS
const ForceColorScheme = () => {
  React.useEffect(() => {
    // Create and inject style element
    const styleElement = document.createElement('style');
    styleElement.textContent = forceDarkModeCSS;
    document.head.appendChild(styleElement);
    
    // Clean up function
    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);
  
  return null;
};

function AppTheme(props) {
  const { children, disableCustomTheme, themeComponents } = props;
  const { mode, systemMode, setMode } = useColorScheme();
  
  // Force any light mode to dark
  React.useEffect(() => {
    if (mode === 'light' || (mode === 'system' && systemMode === 'light')) {
      setMode(mode === 'light' ? 'dark' : mode);
    }
  }, [mode, systemMode, setMode]);
  
  const theme = React.useMemo(() => {
    return disableCustomTheme
      ? {}
      : createTheme({
          // For more details about CSS variables configuration, see https://mui.com/material-ui/customization/css-theme-variables/configuration/
          cssVariables: {
            colorSchemeSelector: 'data-mui-color-scheme',
            cssVarPrefix: 'template',
          },
          colorSchemes, // Recently added in v6 for building light & dark mode app, see https://mui.com/material-ui/customization/palette/#color-schemes
          typography,
          shadows,
          shape,
          components: {
            ...inputsCustomizations,
            ...dataDisplayCustomizations,
            ...feedbackCustomizations,
            ...navigationCustomizations,
            ...surfacesCustomizations,
            ...themeComponents,
          },
        });
  }, [disableCustomTheme, themeComponents]);
  
  if (disableCustomTheme) {
    return <React.Fragment>{children}</React.Fragment>;
  }
  
  return (
    <ThemeProvider theme={theme} disableTransitionOnChange>
      <ForceColorScheme />
      {children}
    </ThemeProvider>
  );
}

AppTheme.propTypes = {
  children: PropTypes.node,
  /**
   * This is for the docs site. You can ignore it or remove it.
   */
  disableCustomTheme: PropTypes.bool,
  themeComponents: PropTypes.object,
};

export default AppTheme;
