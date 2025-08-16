# Layouts Communs de l'Application

## Vue d'ensemble

Les layouts définissent la structure commune des pages de l'application OptimPV, incluant la navigation, les sidebars, headers et footers.

## Structure des Layouts

### 1. Types et Interfaces

```typescript
// types/layout.types.ts
export interface LayoutProps {
  children: React.ReactNode;
  variant?: 'default' | 'dashboard' | 'fullscreen' | 'minimal';
  showSidebar?: boolean;
  showHeader?: boolean;
  showFooter?: boolean;
  sidebarConfig?: SidebarConfig;
  headerConfig?: HeaderConfig;
}

export interface SidebarConfig {
  width?: number;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  position?: 'left' | 'right';
  variant?: 'permanent' | 'temporary' | 'persistent';
  items?: NavigationItem[];
}

export interface HeaderConfig {
  height?: number;
  fixed?: boolean;
  transparent?: boolean;
  showSearch?: boolean;
  showNotifications?: boolean;
  showUserMenu?: boolean;
  customActions?: React.ReactNode;
}

export interface NavigationItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  children?: NavigationItem[];
  badge?: string | number;
  disabled?: boolean;
  divider?: boolean;
  onClick?: () => void;
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: React.ReactNode;
}
```

### 2. Layout Principal

```typescript
// layouts/MainLayout.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Drawer,
  CssBaseline,
  useTheme,
  useMediaQuery,
  Container
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { LayoutProps } from '@/types/layout.types';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Footer } from './components/Footer';
import { useLayout } from '@/hooks/useLayout';

const MainContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'sidebarWidth' && prop !== 'headerHeight'
})<{ sidebarWidth: number; headerHeight: number }>(({ theme, sidebarWidth, headerHeight }) => ({
  display: 'flex',
  minHeight: '100vh',
  backgroundColor: theme.palette.background.default,
  paddingTop: headerHeight,
  transition: theme.transitions.create(['margin', 'padding'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen
  })
}));

const ContentArea = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'sidebarWidth' && prop !== 'showSidebar'
})<{ sidebarWidth: number; showSidebar: boolean }>(({ theme, sidebarWidth, showSidebar }) => ({
  flexGrow: 1,
  marginLeft: showSidebar ? sidebarWidth : 0,
  transition: theme.transitions.create(['margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen
  }),
  [theme.breakpoints.down('sm')]: {
    marginLeft: 0
  }
}));

export const MainLayout: React.FC<LayoutProps> = ({
  children,
  variant = 'default',
  showSidebar = true,
  showHeader = true,
  showFooter = true,
  sidebarConfig = {},
  headerConfig = {}
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useLayout();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    sidebarConfig.defaultCollapsed || false
  );

  const sidebarWidth = sidebarCollapsed ? 64 : (sidebarConfig.width || 240);
  const headerHeight = headerConfig.height || 64;

  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile, setSidebarOpen]);

  const handleSidebarToggle = () => {
    if (isMobile) {
      toggleSidebar();
    } else {
      setSidebarCollapsed(!sidebarCollapsed);
    }
  };

  if (variant === 'fullscreen') {
    return <Box sx={{ minHeight: '100vh' }}>{children}</Box>;
  }

  if (variant === 'minimal') {
    return (
      <Box sx={{ minHeight: '100vh', p: 3 }}>
        <Container maxWidth="lg">{children}</Container>
      </Box>
    );
  }

  return (
    <>
      <CssBaseline />
      <MainContainer sidebarWidth={sidebarWidth} headerHeight={headerHeight}>
        {showHeader && (
          <Header
            config={headerConfig}
            onMenuClick={handleSidebarToggle}
            showMenuButton={showSidebar}
          />
        )}

        {showSidebar && (
          <Sidebar
            config={{
              ...sidebarConfig,
              width: sidebarWidth
            }}
            open={isMobile ? sidebarOpen : true}
            collapsed={sidebarCollapsed}
            onClose={() => setSidebarOpen(false)}
            onCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            isMobile={isMobile}
          />
        )}

        <ContentArea sidebarWidth={sidebarWidth} showSidebar={showSidebar && !isMobile}>
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              minHeight: `calc(100vh - ${headerHeight}px)`,
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <Box sx={{ flexGrow: 1, p: 3 }}>{children}</Box>
            {showFooter && <Footer />}
          </Box>
        </ContentArea>
      </MainContainer>
    </>
  );
};
```

### 3. Dashboard Layout

```typescript
// layouts/DashboardLayout.tsx
import React from 'react';
import { Box, Grid, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';
import { MainLayout } from './MainLayout';
import { Breadcrumbs } from './components/Breadcrumbs';
import { PageHeader } from './components/PageHeader';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  sidebar?: React.ReactNode;
  sidebarWidth?: number;
}

const DashboardContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(3)
}));

const ContentGrid = styled(Grid)(({ theme }) => ({
  flexGrow: 1
}));

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  title,
  subtitle,
  breadcrumbs,
  actions,
  sidebar,
  sidebarWidth = 320
}) => {
  const dashboardItems: NavigationItem[] = [
    {
      id: 'overview',
      label: 'Vue d\'ensemble',
      icon: <Dashboard />,
      path: '/dashboard'
    },
    {
      id: 'projects',
      label: 'Projets',
      icon: <Folder />,
      path: '/projects',
      children: [
        { id: 'all-projects', label: 'Tous les projets', path: '/projects' },
        { id: 'new-project', label: 'Nouveau projet', path: '/projects/new' }
      ]
    },
    {
      id: 'analysis',
      label: 'Analyses',
      icon: <Analytics />,
      path: '/analysis'
    },
    {
      id: 'reports',
      label: 'Rapports',
      icon: <Description />,
      path: '/reports'
    },
    {
      id: 'divider-1',
      divider: true
    },
    {
      id: 'settings',
      label: 'Paramètres',
      icon: <Settings />,
      path: '/settings'
    }
  ];

  return (
    <MainLayout
      variant="dashboard"
      sidebarConfig={{
        items: dashboardItems,
        collapsible: true
      }}
    >
      <DashboardContainer>
        {breadcrumbs && <Breadcrumbs items={breadcrumbs} />}
        
        {(title || actions) && (
          <PageHeader
            title={title}
            subtitle={subtitle}
            actions={actions}
          />
        )}

        <ContentGrid container spacing={3}>
          {sidebar && (
            <Grid item xs={12} md={3} lg={2.5}>
              <Paper sx={{ p: 2, height: '100%', minWidth: sidebarWidth }}>
                {sidebar}
              </Paper>
            </Grid>
          )}
          
          <Grid item xs={12} md={sidebar ? 9 : 12} lg={sidebar ? 9.5 : 12}>
            {children}
          </Grid>
        </ContentGrid>
      </DashboardContainer>
    </MainLayout>
  );
};
```

### 4. Header Component

```typescript
// layouts/components/Header.tsx
import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Badge,
  Divider,
  InputBase,
  Tooltip
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search,
  Notifications,
  AccountCircle,
  Brightness4,
  Brightness7,
  Language,
  Logout
} from '@mui/icons-material';
import { styled, alpha } from '@mui/material/styles';
import { HeaderConfig } from '@/types/layout.types';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';

interface HeaderProps {
  config: HeaderConfig;
  onMenuClick: () => void;
  showMenuButton?: boolean;
}

const StyledAppBar = styled(AppBar, {
  shouldForwardProp: (prop) => prop !== 'transparent'
})<{ transparent?: boolean }>(({ theme, transparent }) => ({
  backgroundColor: transparent ? 'transparent' : theme.palette.background.paper,
  color: theme.palette.text.primary,
  boxShadow: transparent ? 'none' : theme.shadows[1],
  borderBottom: `1px solid ${theme.palette.divider}`,
  zIndex: theme.zIndex.drawer + 1
}));

const SearchBox = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.common.white, 0.15),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.white, 0.25)
  },
  marginRight: theme.spacing(2),
  marginLeft: 0,
  width: '100%',
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(3),
    width: 'auto'
  }
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: 'inherit',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('md')]: {
      width: '20ch',
      '&:focus': {
        width: '30ch'
      }
    }
  }
}));

export const Header: React.FC<HeaderProps> = ({
  config,
  onMenuClick,
  showMenuButton = true
}) => {
  const { user, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchor(null);
  };

  const handleLogout = () => {
    handleUserMenuClose();
    logout();
  };

  return (
    <StyledAppBar
      position={config.fixed ? 'fixed' : 'absolute'}
      transparent={config.transparent}
    >
      <Toolbar sx={{ height: config.height || 64 }}>
        {showMenuButton && (
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={onMenuClick}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}

        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 0 }}>
          OptimPV
        </Typography>

        {config.showSearch !== false && (
          <SearchBox>
            <SearchIconWrapper>
              <Search />
            </SearchIconWrapper>
            <StyledInputBase
              placeholder="Rechercher…"
              inputProps={{ 'aria-label': 'search' }}
            />
          </SearchBox>
        )}

        <Box sx={{ flexGrow: 1 }} />

        {config.customActions}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Changer le thème">
            <IconButton onClick={toggleTheme} color="inherit">
              {isDarkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Langue">
            <IconButton color="inherit">
              <Language />
            </IconButton>
          </Tooltip>

          {config.showNotifications !== false && (
            <IconButton
              color="inherit"
              onClick={handleNotificationOpen}
            >
              <Badge badgeContent={4} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          )}

          {config.showUserMenu !== false && (
            <IconButton
              edge="end"
              onClick={handleUserMenuOpen}
              color="inherit"
            >
              <Avatar
                alt={user?.name}
                src={user?.avatar}
                sx={{ width: 32, height: 32 }}
              >
                {user?.name?.charAt(0).toUpperCase()}
              </Avatar>
            </IconButton>
          )}
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle1">{user?.name}</Typography>
            <Typography variant="body2" color="textSecondary">
              {user?.email}
            </Typography>
          </Box>
          <Divider />
          <MenuItem onClick={handleUserMenuClose}>
            <AccountCircle sx={{ mr: 1 }} /> Mon profil
          </MenuItem>
          <MenuItem onClick={handleUserMenuClose}>
            <Settings sx={{ mr: 1 }} /> Paramètres
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <Logout sx={{ mr: 1 }} /> Déconnexion
          </MenuItem>
        </Menu>

        <NotificationPanel
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={handleNotificationClose}
        />
      </Toolbar>
    </StyledAppBar>
  );
};
```

### 5. Sidebar Component

```typescript
// layouts/components/Sidebar.tsx
import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
  Box,
  IconButton,
  Typography,
  Tooltip,
  Badge
} from '@mui/material';
import {
  ExpandLess,
  ExpandMore,
  ChevronLeft,
  ChevronRight
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useLocation, useNavigate } from 'react-router-dom';
import { SidebarConfig, NavigationItem } from '@/types/layout.types';

interface SidebarProps {
  config: SidebarConfig;
  open: boolean;
  collapsed: boolean;
  onClose: () => void;
  onCollapse: () => void;
  isMobile: boolean;
}

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: 'space-between'
}));

const StyledDrawer = styled(Drawer, {
  shouldForwardProp: (prop) => prop !== 'width'
})<{ width: number }>(({ theme, width }) => ({
  width: width,
  flexShrink: 0,
  whiteSpace: 'nowrap',
  boxSizing: 'border-box',
  '& .MuiDrawer-paper': {
    width: width,
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen
    }),
    overflowX: 'hidden'
  }
}));

export const Sidebar: React.FC<SidebarProps> = ({
  config,
  open,
  collapsed,
  onClose,
  onCollapse,
  isMobile
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const handleItemClick = (item: NavigationItem) => {
    if (item.onClick) {
      item.onClick();
    } else if (item.path) {
      navigate(item.path);
      if (isMobile) {
        onClose();
      }
    } else if (item.children) {
      setExpandedItems(prev =>
        prev.includes(item.id)
          ? prev.filter(id => id !== item.id)
          : [...prev, item.id]
      );
    }
  };

  const isItemActive = (item: NavigationItem): boolean => {
    if (item.path) {
      return location.pathname === item.path;
    }
    if (item.children) {
      return item.children.some(child => isItemActive(child));
    }
    return false;
  };

  const renderNavigationItem = (item: NavigationItem, depth = 0) => {
    if (item.divider) {
      return <Divider key={item.id} sx={{ my: 1 }} />;
    }

    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.id);
    const isActive = isItemActive(item);

    return (
      <React.Fragment key={item.id}>
        <ListItem disablePadding sx={{ display: 'block' }}>
          <Tooltip
            title={collapsed && !isMobile ? item.label : ''}
            placement="right"
          >
            <ListItemButton
              onClick={() => handleItemClick(item)}
              disabled={item.disabled}
              selected={isActive}
              sx={{
                minHeight: 48,
                justifyContent: collapsed && !isMobile ? 'center' : 'initial',
                px: 2.5,
                pl: depth > 0 ? depth * 4 : 2.5
              }}
            >
              {item.icon && (
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: collapsed && !isMobile ? 0 : 3,
                    justifyContent: 'center'
                  }}
                >
                  {item.badge ? (
                    <Badge badgeContent={item.badge} color="error">
                      {item.icon}
                    </Badge>
                  ) : (
                    item.icon
                  )}
                </ListItemIcon>
              )}
              
              {(!collapsed || isMobile) && (
                <>
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{
                      fontSize: depth > 0 ? 14 : 16
                    }}
                  />
                  {hasChildren && (
                    isExpanded ? <ExpandLess /> : <ExpandMore />
                  )}
                </>
              )}
            </ListItemButton>
          </Tooltip>
        </ListItem>

        {hasChildren && (!collapsed || isMobile) && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavigationItem(child, depth + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <StyledDrawer
      variant={isMobile ? 'temporary' : config.variant || 'permanent'}
      open={open}
      onClose={onClose}
      width={config.width || 240}
      ModalProps={{
        keepMounted: true // Better open performance on mobile
      }}
    >
      <DrawerHeader>
        {(!collapsed || isMobile) && (
          <Box sx={{ display: 'flex', alignItems: 'center', pl: 1 }}>
            <img src="/logo.png" alt="Logo" style={{ height: 32 }} />
            <Typography variant="h6" sx={{ ml: 1 }}>
              OptimPV
            </Typography>
          </Box>
        )}
        
        {config.collapsible && !isMobile && (
          <IconButton onClick={onCollapse}>
            {collapsed ? <ChevronRight /> : <ChevronLeft />}
          </IconButton>
        )}
      </DrawerHeader>

      <Divider />

      <List>
        {config.items?.map(item => renderNavigationItem(item))}
      </List>
    </StyledDrawer>
  );
};
```

### 6. Page Layout avec Tabs

```typescript
// layouts/PageWithTabs.tsx
import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
  Breadcrumbs,
  Link
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { MainLayout } from './MainLayout';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

interface PageTab {
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

interface PageWithTabsProps {
  title: string;
  subtitle?: string;
  tabs: PageTab[];
  defaultTab?: number;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
}

const PageContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  gap: theme.spacing(2)
}));

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      sx={{ flexGrow: 1 }}
    >
      {value === index && children}
    </Box>
  );
};

export const PageWithTabs: React.FC<PageWithTabsProps> = ({
  title,
  subtitle,
  tabs,
  defaultTab = 0,
  breadcrumbs,
  actions
}) => {
  const [currentTab, setCurrentTab] = useState(defaultTab);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <MainLayout>
      <PageContainer>
        {breadcrumbs && (
          <Breadcrumbs aria-label="breadcrumb">
            {breadcrumbs.map((crumb, index) => (
              <Link
                key={index}
                color={index === breadcrumbs.length - 1 ? 'text.primary' : 'inherit'}
                href={crumb.path}
                underline={index === breadcrumbs.length - 1 ? 'none' : 'hover'}
              >
                {crumb.label}
              </Link>
            ))}
          </Breadcrumbs>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body1" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {actions}
        </Box>

        <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            {tabs.map((tab, index) => (
              <Tab
                key={index}
                label={tab.label}
                icon={tab.icon}
                iconPosition="start"
                disabled={tab.disabled}
                id={`tab-${index}`}
                aria-controls={`tabpanel-${index}`}
              />
            ))}
          </Tabs>

          <Box sx={{ flexGrow: 1, p: 3 }}>
            {tabs.map((tab, index) => (
              <TabPanel key={index} value={currentTab} index={index}>
                {tab.content}
              </TabPanel>
            ))}
          </Box>
        </Paper>
      </PageContainer>
    </MainLayout>
  );
};
```

### 7. Split Layout

```typescript
// layouts/SplitLayout.tsx
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { ChevronLeft, ChevronRight } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { MainLayout } from './MainLayout';

interface SplitLayoutProps {
  left: React.ReactNode;
  right: React.ReactNode;
  leftWidth?: number | string;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  resizable?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

const SplitContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  height: '100%',
  gap: theme.spacing(2),
  [theme.breakpoints.down('md')]: {
    flexDirection: 'column'
  }
}));

const Panel = styled(Paper)(({ theme }) => ({
  overflow: 'auto',
  position: 'relative'
}));

const ResizeHandle = styled(Box)(({ theme }) => ({
  width: 4,
  cursor: 'col-resize',
  backgroundColor: theme.palette.divider,
  '&:hover': {
    backgroundColor: theme.palette.primary.main
  },
  transition: 'background-color 0.2s'
}));

const CollapseButton = styled(IconButton)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(1),
  right: theme.spacing(1),
  zIndex: 1
}));

export const SplitLayout: React.FC<SplitLayoutProps> = ({
  left,
  right,
  leftWidth = 400,
  minLeftWidth = 200,
  maxLeftWidth = 600,
  resizable = true,
  collapsible = true,
  defaultCollapsed = false
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [width, setWidth] = useState(leftWidth);
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [isResizing, setIsResizing] = useState(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!resizable || isMobile) return;
    
    setIsResizing(true);
    const startX = e.clientX;
    const startWidth = width;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = startWidth + (e.clientX - startX);
      const clampedWidth = Math.max(minLeftWidth, Math.min(maxLeftWidth, newWidth));
      setWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const toggleCollapse = () => {
    setCollapsed(!collapsed);
  };

  if (isMobile) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>
          <Panel sx={{ p: 2 }}>{left}</Panel>
          <Divider />
          <Panel sx={{ p: 2, flexGrow: 1 }}>{right}</Panel>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <SplitContainer>
        {!collapsed && (
          <>
            <Panel
              sx={{
                width: width,
                minWidth: minLeftWidth,
                maxWidth: maxLeftWidth,
                p: 2,
                position: 'relative'
              }}
            >
              {collapsible && (
                <CollapseButton onClick={toggleCollapse} size="small">
                  <ChevronLeft />
                </CollapseButton>
              )}
              {left}
            </Panel>

            {resizable && (
              <ResizeHandle
                onMouseDown={handleMouseDown}
                sx={{
                  cursor: isResizing ? 'col-resize' : 'auto',
                  userSelect: isResizing ? 'none' : 'auto'
                }}
              />
            )}
          </>
        )}

        <Panel sx={{ flexGrow: 1, p: 2, position: 'relative' }}>
          {collapsed && collapsible && (
            <CollapseButton onClick={toggleCollapse} size="small">
              <ChevronRight />
            </CollapseButton>
          )}
          {right}
        </Panel>
      </SplitContainer>
    </MainLayout>
  );
};
```

### 8. Hook de Layout

```typescript
// hooks/useLayout.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface LayoutState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  headerHeight: number;
  sidebarWidth: number;
  isDarkMode: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarCollapse: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setHeaderHeight: (height: number) => void;
  setSidebarWidth: (width: number) => void;
  toggleTheme: () => void;
  setDarkMode: (isDark: boolean) => void;
}

export const useLayout = create<LayoutState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      sidebarCollapsed: false,
      headerHeight: 64,
      sidebarWidth: 240,
      isDarkMode: false,

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      toggleSidebarCollapse: () => set((state) => ({ 
        sidebarCollapsed: !state.sidebarCollapsed 
      })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      setHeaderHeight: (height) => set({ headerHeight: height }),
      setSidebarWidth: (width) => set({ sidebarWidth: width }),

      toggleTheme: () => set((state) => ({ isDarkMode: !state.isDarkMode })),
      setDarkMode: (isDark) => set({ isDarkMode: isDark })
    }),
    {
      name: 'layout-storage',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        isDarkMode: state.isDarkMode
      })
    }
  )
);
```

## Utilisation des Layouts

### Exemple d'utilisation

```typescript
// pages/ProjectAnalysis.tsx
import React from 'react';
import { PageWithTabs } from '@/layouts/PageWithTabs';
import { FinancialAnalysis } from '@/components/analysis/FinancialAnalysis';
import { TechnicalAnalysis } from '@/components/analysis/TechnicalAnalysis';
import { EnvironmentalImpact } from '@/components/analysis/EnvironmentalImpact';
import { Button } from '@/components/shared';
import { Download, Share } from '@mui/icons-material';

export const ProjectAnalysis: React.FC = () => {
  const tabs = [
    {
      label: 'Analyse Financière',
      icon: <TrendingUp />,
      content: <FinancialAnalysis />
    },
    {
      label: 'Analyse Technique',
      icon: <Engineering />,
      content: <TechnicalAnalysis />
    },
    {
      label: 'Impact Environnemental',
      icon: <Eco />,
      content: <EnvironmentalImpact />
    }
  ];

  return (
    <PageWithTabs
      title="Analyse du Projet Solar Park Alpha"
      subtitle="Analyse complète du projet photovoltaïque"
      tabs={tabs}
      breadcrumbs={[
        { label: 'Projets', path: '/projects' },
        { label: 'Solar Park Alpha', path: '/projects/123' },
        { label: 'Analyse' }
      ]}
      actions={
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button startIcon={<Share />} variant="secondary">
            Partager
          </Button>
          <Button startIcon={<Download />}>
            Exporter
          </Button>
        </Box>
      }
    />
  );
};
```

## Best Practices

1. **Responsive Design** : Tous les layouts s'adaptent automatiquement aux différentes tailles d'écran
2. **Persistance** : Les préférences utilisateur (sidebar collapse, theme) sont sauvegardées
3. **Performance** : Utilisation de React.memo et lazy loading pour les grandes applications
4. **Accessibilité** : Support complet de la navigation au clavier et des lecteurs d'écran
5. **Customisation** : Props flexibles pour adapter les layouts aux besoins spécifiques

## Export Central

```typescript
// layouts/index.ts
export { MainLayout } from './MainLayout';
export { DashboardLayout } from './DashboardLayout';
export { PageWithTabs } from './PageWithTabs';
export { SplitLayout } from './SplitLayout';
export { useLayout } from '../hooks/useLayout';
```