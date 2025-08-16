# Composants UI Réutilisables

## Vue d'ensemble

Cette bibliothèque de composants fournit des éléments d'interface réutilisables, cohérents et accessibles pour l'ensemble de l'application OptimPV.

## Structure des Composants

### 1. Système de Types Communs

```typescript
// types/shared.types.ts
export type Variant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
export type Size = 'small' | 'medium' | 'large';
export type Status = 'idle' | 'loading' | 'success' | 'error';

export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  id?: string;
  testId?: string;
}

export interface LoadingState {
  isLoading: boolean;
  progress?: number;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  error?: Error | string;
  retry?: () => void;
}
```

### 2. Boutons

```typescript
// components/shared/Button/Button.tsx
import React, { forwardRef } from 'react';
import { Button as MuiButton, CircularProgress } from '@mui/material';
import { styled } from '@mui/material/styles';
import { BaseComponentProps, Variant, Size } from '@/types/shared.types';

interface ButtonProps extends BaseComponentProps {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
  loading?: boolean;
  disabled?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
}

const StyledButton = styled(MuiButton, {
  shouldForwardProp: (prop) => prop !== 'loading'
})<{ loading?: boolean }>(({ theme, loading }) => ({
  position: 'relative',
  '&.Mui-disabled': {
    backgroundColor: loading ? theme.palette.action.disabledBackground : undefined
  },
  '& .MuiButton-startIcon, & .MuiButton-endIcon': {
    opacity: loading ? 0 : 1
  }
}));

const LoadingSpinner = styled(CircularProgress)({
  position: 'absolute',
  top: '50%',
  left: '50%',
  marginTop: -12,
  marginLeft: -12
});

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'medium',
      fullWidth = false,
      loading = false,
      disabled = false,
      startIcon,
      endIcon,
      children,
      onClick,
      type = 'button',
      className,
      testId,
      ...props
    },
    ref
  ) => {
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (!loading && !disabled && onClick) {
        onClick(event);
      }
    };

    return (
      <StyledButton
        ref={ref}
        variant={variant === 'primary' ? 'contained' : 'outlined'}
        color={variant as any}
        size={size}
        fullWidth={fullWidth}
        disabled={disabled || loading}
        loading={loading}
        startIcon={!loading ? startIcon : undefined}
        endIcon={!loading ? endIcon : undefined}
        onClick={handleClick}
        type={type}
        className={className}
        data-testid={testId}
        {...props}
      >
        {children}
        {loading && <LoadingSpinner size={24} />}
      </StyledButton>
    );
  }
);

Button.displayName = 'Button';

// Variantes spécialisées
export const IconButton = styled(MuiButton)(({ theme }) => ({
  minWidth: 'auto',
  padding: theme.spacing(1),
  borderRadius: '50%'
}));

export const TextButton = styled(MuiButton)(({ theme }) => ({
  textTransform: 'none',
  fontWeight: 'normal',
  '&:hover': {
    backgroundColor: 'transparent',
    textDecoration: 'underline'
  }
}));
```

### 3. Cards

```typescript
// components/shared/Card/Card.tsx
import React from 'react';
import {
  Card as MuiCard,
  CardContent,
  CardHeader,
  CardActions,
  Collapse,
  IconButton,
  Skeleton
} from '@mui/material';
import { ExpandMore, MoreVert } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { BaseComponentProps } from '@/types/shared.types';

interface CardProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
  avatar?: React.ReactNode;
  action?: React.ReactNode;
  expandable?: boolean;
  defaultExpanded?: boolean;
  loading?: boolean;
  elevated?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
  onActionClick?: () => void;
}

const StyledCard = styled(MuiCard, {
  shouldForwardProp: (prop) => prop !== 'elevated'
})<{ elevated?: boolean }>(({ theme, elevated }) => ({
  transition: 'all 0.3s ease',
  ...(elevated && {
    '&:hover': {
      boxShadow: theme.shadows[8],
      transform: 'translateY(-4px)'
    }
  })
}));

const ExpandButton = styled(IconButton, {
  shouldForwardProp: (prop) => prop !== 'expanded'
})<{ expanded: boolean }>(({ theme, expanded }) => ({
  transform: !expanded ? 'rotate(0deg)' : 'rotate(180deg)',
  marginLeft: 'auto',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest
  })
}));

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  avatar,
  action,
  expandable = false,
  defaultExpanded = false,
  loading = false,
  elevated = false,
  children,
  footer,
  onActionClick,
  className,
  testId,
  ...props
}) => {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  if (loading) {
    return (
      <StyledCard className={className} data-testid={testId} {...props}>
        <CardHeader
          avatar={<Skeleton variant="circular" width={40} height={40} />}
          title={<Skeleton variant="text" width="60%" />}
          subheader={<Skeleton variant="text" width="40%" />}
        />
        <CardContent>
          <Skeleton variant="rectangular" height={100} />
        </CardContent>
      </StyledCard>
    );
  }

  return (
    <StyledCard elevated={elevated} className={className} data-testid={testId} {...props}>
      {(title || subtitle || avatar || action) && (
        <CardHeader
          avatar={avatar}
          action={
            action || (onActionClick && (
              <IconButton onClick={onActionClick}>
                <MoreVert />
              </IconButton>
            ))
          }
          title={title}
          subheader={subtitle}
        />
      )}

      <CardContent>
        {expandable ? (
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            {children}
          </Collapse>
        ) : (
          children
        )}
      </CardContent>

      {(footer || expandable) && (
        <CardActions disableSpacing>
          {footer}
          {expandable && (
            <ExpandButton
              expanded={expanded}
              onClick={handleExpandClick}
              aria-expanded={expanded}
              aria-label="show more"
            >
              <ExpandMore />
            </ExpandButton>
          )}
        </CardActions>
      )}
    </StyledCard>
  );
};

// Variantes spécialisées
export const MetricCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  loading?: boolean;
}> = ({ title, value, change, icon, loading }) => {
  const isPositive = change && change > 0;

  return (
    <Card loading={loading}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="body2" color="textSecondary">
            {title}
          </Typography>
          <Typography variant="h4" sx={{ mt: 1 }}>
            {value}
          </Typography>
          {change !== undefined && (
            <Typography
              variant="body2"
              sx={{
                mt: 1,
                color: isPositive ? 'success.main' : 'error.main',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              {isPositive ? <TrendingUp /> : <TrendingDown />}
              {Math.abs(change)}%
            </Typography>
          )}
        </Box>
        {icon && (
          <Box sx={{ color: 'primary.main', opacity: 0.3 }}>
            {icon}
          </Box>
        )}
      </Box>
    </Card>
  );
};
```

### 4. Inputs

```typescript
// components/shared/Input/Input.tsx
import React, { forwardRef } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  FormHelperText,
  Box
} from '@mui/material';
import { Visibility, VisibilityOff, Clear } from '@mui/icons-material';
import { BaseComponentProps } from '@/types/shared.types';

interface InputProps extends BaseComponentProps {
  label?: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  placeholder?: string;
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  fullWidth?: boolean;
  multiline?: boolean;
  rows?: number;
  maxRows?: number;
  startAdornment?: React.ReactNode;
  endAdornment?: React.ReactNode;
  clearable?: boolean;
  maxLength?: number;
  min?: number;
  max?: number;
  step?: number;
  autoComplete?: string;
  autoFocus?: boolean;
  onBlur?: () => void;
  onFocus?: () => void;
  onKeyPress?: (event: React.KeyboardEvent) => void;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      value,
      onChange,
      type = 'text',
      placeholder,
      error = false,
      helperText,
      disabled = false,
      required = false,
      fullWidth = true,
      multiline = false,
      rows,
      maxRows,
      startAdornment,
      endAdornment,
      clearable = false,
      maxLength,
      min,
      max,
      step,
      autoComplete,
      autoFocus = false,
      onBlur,
      onFocus,
      onKeyPress,
      className,
      testId,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = React.useState(false);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = event.target.value;
      
      // Validation pour les types numériques
      if (type === 'number') {
        const numValue = parseFloat(newValue);
        if (!isNaN(numValue)) {
          if (min !== undefined && numValue < min) return;
          if (max !== undefined && numValue > max) return;
        }
      }

      // Validation de la longueur maximale
      if (maxLength && newValue.length > maxLength) return;

      onChange(newValue);
    };

    const handleClear = () => {
      onChange('');
    };

    const togglePasswordVisibility = () => {
      setShowPassword(!showPassword);
    };

    const inputType = type === 'password' && showPassword ? 'text' : type;

    const renderEndAdornment = () => {
      const adornments = [];

      if (clearable && value && !disabled) {
        adornments.push(
          <IconButton
            key="clear"
            onClick={handleClear}
            edge="end"
            size="small"
            tabIndex={-1}
          >
            <Clear fontSize="small" />
          </IconButton>
        );
      }

      if (type === 'password') {
        adornments.push(
          <IconButton
            key="password"
            onClick={togglePasswordVisibility}
            edge="end"
            size="small"
            tabIndex={-1}
          >
            {showPassword ? <VisibilityOff /> : <Visibility />}
          </IconButton>
        );
      }

      if (endAdornment) {
        adornments.push(endAdornment);
      }

      return adornments.length > 0 ? (
        <InputAdornment position="end">
          {adornments}
        </InputAdornment>
      ) : null;
    };

    return (
      <Box className={className}>
        <TextField
          ref={ref}
          label={label}
          value={value}
          onChange={handleChange}
          type={inputType}
          placeholder={placeholder}
          error={error}
          helperText={helperText}
          disabled={disabled}
          required={required}
          fullWidth={fullWidth}
          multiline={multiline}
          rows={rows}
          maxRows={maxRows}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          onBlur={onBlur}
          onFocus={onFocus}
          onKeyPress={onKeyPress}
          inputProps={{
            'data-testid': testId,
            min,
            max,
            step,
            maxLength
          }}
          InputProps={{
            startAdornment: startAdornment && (
              <InputAdornment position="start">{startAdornment}</InputAdornment>
            ),
            endAdornment: renderEndAdornment()
          }}
          {...props}
        />
        {maxLength && (
          <FormHelperText
            sx={{ textAlign: 'right', mt: 0.5 }}
            error={error}
          >
            {value.toString().length}/{maxLength}
          </FormHelperText>
        )}
      </Box>
    );
  }
);

Input.displayName = 'Input';

// Composants spécialisés
export const SearchInput: React.FC<{
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onSearch?: () => void;
}> = ({ value, onChange, placeholder = 'Rechercher...', onSearch }) => {
  return (
    <Input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      startAdornment={<Search />}
      clearable
      onKeyPress={(e) => {
        if (e.key === 'Enter' && onSearch) {
          onSearch();
        }
      }}
    />
  );
};

export const CurrencyInput: React.FC<{
  value: number;
  onChange: (value: number) => void;
  currency?: string;
  label?: string;
}> = ({ value, onChange, currency = '€', label }) => {
  return (
    <Input
      type="number"
      value={value}
      onChange={(v) => onChange(parseFloat(v) || 0)}
      label={label}
      endAdornment={currency}
      min={0}
      step={0.01}
    />
  );
};
```

### 5. Modals

```typescript
// components/shared/Modal/Modal.tsx
import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  Slide
} from '@mui/material';
import { Close } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { BaseComponentProps, Size } from '@/types/shared.types';

interface ModalProps extends BaseComponentProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  size?: Size | 'fullscreen';
  children: React.ReactNode;
  actions?: React.ReactNode;
  closeButton?: boolean;
  disableBackdropClick?: boolean;
  disableEscapeKeyDown?: boolean;
  TransitionComponent?: React.ComponentType;
}

const StyledDialogTitle = styled(DialogTitle)(({ theme }) => ({
  margin: 0,
  padding: theme.spacing(2),
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between'
}));

const StyledDialogContent = styled(DialogContent)(({ theme }) => ({
  padding: theme.spacing(2),
  '&:first-of-type': {
    paddingTop: theme.spacing(2)
  }
}));

const Transition = React.forwardRef(function Transition(
  props: any,
  ref: React.Ref<unknown>
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

export const Modal: React.FC<ModalProps> = ({
  open,
  onClose,
  title,
  subtitle,
  size = 'medium',
  children,
  actions,
  closeButton = true,
  disableBackdropClick = false,
  disableEscapeKeyDown = false,
  TransitionComponent = Transition,
  className,
  testId,
  ...props
}) => {
  const handleClose = (event: any, reason: string) => {
    if (
      (reason === 'backdropClick' && disableBackdropClick) ||
      (reason === 'escapeKeyDown' && disableEscapeKeyDown)
    ) {
      return;
    }
    onClose();
  };

  const getMaxWidth = () => {
    switch (size) {
      case 'small':
        return 'xs';
      case 'medium':
        return 'sm';
      case 'large':
        return 'md';
      case 'fullscreen':
        return false;
      default:
        return 'sm';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={getMaxWidth()}
      fullWidth
      fullScreen={size === 'fullscreen'}
      TransitionComponent={TransitionComponent}
      className={className}
      data-testid={testId}
      {...props}
    >
      {(title || subtitle || closeButton) && (
        <StyledDialogTitle>
          <Box>
            {title && (
              <Typography variant="h6" component="div">
                {title}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {closeButton && (
            <IconButton
              aria-label="close"
              onClick={onClose}
              sx={{ marginLeft: 2 }}
            >
              <Close />
            </IconButton>
          )}
        </StyledDialogTitle>
      )}

      <StyledDialogContent>{children}</StyledDialogContent>

      {actions && <DialogActions>{actions}</DialogActions>}
    </Dialog>
  );
};

// Modal de confirmation
export const ConfirmModal: React.FC<{
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'info' | 'warning' | 'error';
}> = ({
  open,
  onClose,
  onConfirm,
  title = 'Confirmation',
  message,
  confirmText = 'Confirmer',
  cancelText = 'Annuler',
  variant = 'info'
}) => {
  const getIcon = () => {
    switch (variant) {
      case 'warning':
        return <Warning color="warning" sx={{ fontSize: 48 }} />;
      case 'error':
        return <Error color="error" sx={{ fontSize: 48 }} />;
      default:
        return <Info color="info" sx={{ fontSize: 48 }} />;
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      size="small"
      actions={
        <>
          <Button onClick={onClose} variant="secondary">
            {cancelText}
          </Button>
          <Button onClick={onConfirm} variant={variant}>
            {confirmText}
          </Button>
        </>
      }
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {getIcon()}
        <Typography>{message}</Typography>
      </Box>
    </Modal>
  );
};
```

### 6. Tables

```typescript
// components/shared/Table/Table.tsx
import React, { useState } from 'react';
import {
  Table as MuiTable,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Checkbox,
  Paper,
  Skeleton,
  Box,
  Typography
} from '@mui/material';
import { BaseComponentProps } from '@/types/shared.types';

interface Column<T> {
  id: keyof T;
  label: string;
  align?: 'left' | 'center' | 'right';
  width?: string | number;
  sortable?: boolean;
  format?: (value: any, row: T) => React.ReactNode;
}

interface TableProps<T> extends BaseComponentProps {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: Error | null;
  emptyMessage?: string;
  selectable?: boolean;
  selected?: string[];
  onSelectionChange?: (selected: string[]) => void;
  sortable?: boolean;
  defaultOrderBy?: keyof T;
  defaultOrder?: 'asc' | 'desc';
  pageable?: boolean;
  pageSize?: number;
  pageSizeOptions?: number[];
  stickyHeader?: boolean;
  maxHeight?: number;
  onRowClick?: (row: T) => void;
  getRowId?: (row: T) => string;
}

export function Table<T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  error = null,
  emptyMessage = 'Aucune donnée disponible',
  selectable = false,
  selected = [],
  onSelectionChange,
  sortable = true,
  defaultOrderBy,
  defaultOrder = 'asc',
  pageable = true,
  pageSize = 10,
  pageSizeOptions = [5, 10, 25, 50],
  stickyHeader = false,
  maxHeight,
  onRowClick,
  getRowId = (row) => row.id,
  className,
  testId,
  ...props
}: TableProps<T>) {
  const [order, setOrder] = useState<'asc' | 'desc'>(defaultOrder);
  const [orderBy, setOrderBy] = useState<keyof T | undefined>(defaultOrderBy);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(pageSize);

  const handleSort = (column: keyof T) => {
    const isAsc = orderBy === column && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(column);
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = data.map((row) => getRowId(row));
      onSelectionChange?.(newSelected);
    } else {
      onSelectionChange?.([]);
    }
  };

  const handleSelectRow = (id: string) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }

    onSelectionChange?.(newSelected);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Tri des données
  const sortedData = React.useMemo(() => {
    if (!sortable || !orderBy) return data;

    return [...data].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];

      if (aValue < bValue) {
        return order === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return order === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, order, orderBy, sortable]);

  // Pagination des données
  const paginatedData = pageable
    ? sortedData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
    : sortedData;

  if (loading) {
    return (
      <TableContainer component={Paper}>
        <MuiTable>
          <TableHead>
            <TableRow>
              {selectable && <TableCell padding="checkbox" />}
              {columns.map((column) => (
                <TableCell key={String(column.id)}>{column.label}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {[...Array(5)].map((_, index) => (
              <TableRow key={index}>
                {selectable && (
                  <TableCell padding="checkbox">
                    <Skeleton variant="rectangular" width={20} height={20} />
                  </TableCell>
                )}
                {columns.map((column) => (
                  <TableCell key={String(column.id)}>
                    <Skeleton variant="text" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </MuiTable>
      </TableContainer>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error">Erreur: {error.message}</Typography>
      </Box>
    );
  }

  const isSelected = (id: string) => selected.indexOf(id) !== -1;

  return (
    <Paper className={className} data-testid={testId} {...props}>
      <TableContainer sx={{ maxHeight }}>
        <MuiTable stickyHeader={stickyHeader}>
          <TableHead>
            <TableRow>
              {selectable && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selected.length > 0 && selected.length < data.length}
                    checked={data.length > 0 && selected.length === data.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
              )}
              {columns.map((column) => (
                <TableCell
                  key={String(column.id)}
                  align={column.align}
                  style={{ width: column.width }}
                  sortDirection={orderBy === column.id ? order : false}
                >
                  {sortable && column.sortable !== false ? (
                    <TableSortLabel
                      active={orderBy === column.id}
                      direction={orderBy === column.id ? order : 'asc'}
                      onClick={() => handleSort(column.id)}
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.length > 0 ? (
              paginatedData.map((row) => {
                const rowId = getRowId(row);
                const isItemSelected = isSelected(rowId);

                return (
                  <TableRow
                    key={rowId}
                    hover
                    onClick={() => onRowClick?.(row)}
                    selected={isItemSelected}
                    sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                  >
                    {selectable && (
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={isItemSelected}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectRow(rowId);
                          }}
                        />
                      </TableCell>
                    )}
                    {columns.map((column) => (
                      <TableCell key={String(column.id)} align={column.align}>
                        {column.format
                          ? column.format(row[column.id], row)
                          : row[column.id]}
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  align="center"
                >
                  <Typography variant="body2" color="textSecondary">
                    {emptyMessage}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </MuiTable>
      </TableContainer>
      {pageable && data.length > 0 && (
        <TablePagination
          rowsPerPageOptions={pageSizeOptions}
          component="div"
          count={data.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Lignes par page:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} sur ${count !== -1 ? count : `plus de ${to}`}`
          }
        />
      )}
    </Paper>
  );
}
```

### 7. Notifications

```typescript
// components/shared/Notification/Notification.tsx
import React from 'react';
import { Alert, Snackbar, AlertTitle, IconButton } from '@mui/material';
import { Close } from '@mui/icons-material';
import { Variant } from '@/types/shared.types';

interface NotificationProps {
  open: boolean;
  onClose: () => void;
  message: string;
  title?: string;
  variant?: Variant;
  duration?: number;
  position?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'center' | 'right';
  };
  action?: React.ReactNode;
}

export const Notification: React.FC<NotificationProps> = ({
  open,
  onClose,
  message,
  title,
  variant = 'info',
  duration = 6000,
  position = { vertical: 'top', horizontal: 'right' },
  action
}) => {
  const getSeverity = () => {
    switch (variant) {
      case 'primary':
      case 'secondary':
        return 'info';
      default:
        return variant as any;
    }
  };

  return (
    <Snackbar
      open={open}
      autoHideDuration={duration}
      onClose={onClose}
      anchorOrigin={position}
    >
      <Alert
        onClose={onClose}
        severity={getSeverity()}
        sx={{ width: '100%' }}
        action={
          action || (
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={onClose}
            >
              <Close fontSize="small" />
            </IconButton>
          )
        }
      >
        {title && <AlertTitle>{title}</AlertTitle>}
        {message}
      </Alert>
    </Snackbar>
  );
};

// Hook pour gérer les notifications
export const useNotification = () => {
  const [notifications, setNotifications] = React.useState<
    Array<{
      id: string;
      message: string;
      title?: string;
      variant?: Variant;
    }>
  >([]);

  const notify = React.useCallback(
    (
      message: string,
      options?: {
        title?: string;
        variant?: Variant;
      }
    ) => {
      const id = Date.now().toString();
      setNotifications((prev) => [
        ...prev,
        {
          id,
          message,
          ...options
        }
      ]);
    },
    []
  );

  const removeNotification = React.useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  return { notifications, notify, removeNotification };
};
```

### 8. Loading States

```typescript
// components/shared/Loading/Loading.tsx
import React from 'react';
import {
  Box,
  CircularProgress,
  LinearProgress,
  Typography,
  Backdrop
} from '@mui/material';
import { styled } from '@mui/material/styles';

interface LoadingProps {
  type?: 'circular' | 'linear' | 'skeleton';
  size?: 'small' | 'medium' | 'large';
  message?: string;
  progress?: number;
  fullscreen?: boolean;
}

const LoadingContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(3)
}));

export const Loading: React.FC<LoadingProps> = ({
  type = 'circular',
  size = 'medium',
  message,
  progress,
  fullscreen = false
}) => {
  const getSize = () => {
    switch (size) {
      case 'small':
        return 20;
      case 'large':
        return 60;
      default:
        return 40;
    }
  };

  const content = (
    <LoadingContainer>
      {type === 'circular' && (
        <CircularProgress
          size={getSize()}
          variant={progress !== undefined ? 'determinate' : 'indeterminate'}
          value={progress}
        />
      )}
      {type === 'linear' && (
        <Box sx={{ width: '100%', minWidth: 200 }}>
          <LinearProgress
            variant={progress !== undefined ? 'determinate' : 'indeterminate'}
            value={progress}
          />
        </Box>
      )}
      {message && (
        <Typography
          variant="body2"
          color="textSecondary"
          sx={{ mt: 2, textAlign: 'center' }}
        >
          {message}
        </Typography>
      )}
      {progress !== undefined && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
          {Math.round(progress)}%
        </Typography>
      )}
    </LoadingContainer>
  );

  if (fullscreen) {
    return (
      <Backdrop open sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        {content}
      </Backdrop>
    );
  }

  return content;
};

// Composant de chargement paresseux
export const LazyLoadBoundary: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = <Loading /> }) => {
  return (
    <React.Suspense fallback={fallback}>
      {children}
    </React.Suspense>
  );
};
```

## Utilisation des Composants

### Exemple d'intégration

```typescript
// pages/ProjectDashboard.tsx
import React from 'react';
import { Grid, Box } from '@mui/material';
import {
  Button,
  Card,
  MetricCard,
  Table,
  Input,
  SearchInput,
  Modal,
  useNotification
} from '@/components/shared';

export const ProjectDashboard: React.FC = () => {
  const { notify } = useNotification();
  const [searchQuery, setSearchQuery] = useState('');
  const [modalOpen, setModalOpen] = useState(false);

  const handleSaveProject = async () => {
    try {
      // Logique de sauvegarde
      notify('Projet sauvegardé avec succès', { variant: 'success' });
    } catch (error) {
      notify('Erreur lors de la sauvegarde', { variant: 'error' });
    }
  };

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card
            title="Tableau de bord du projet"
            subtitle="Vue d'ensemble des métriques clés"
            action={
              <Button onClick={() => setModalOpen(true)}>
                Nouveau projet
              </Button>
            }
          >
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Rechercher un projet..."
            />
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <MetricCard
            title="Production annuelle"
            value="45,230 kWh"
            change={12.5}
            icon={<SolarPower />}
          />
        </Grid>

        <Grid item xs={12}>
          <Table
            columns={[
              { id: 'name', label: 'Nom du projet' },
              { id: 'power', label: 'Puissance (kWc)', align: 'right' },
              { id: 'status', label: 'Statut' }
            ]}
            data={projects}
            selectable
            onRowClick={(row) => console.log('Selected:', row)}
          />
        </Grid>
      </Grid>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Nouveau projet"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleSaveProject}>
              Créer
            </Button>
          </>
        }
      >
        <Input
          label="Nom du projet"
          value={projectName}
          onChange={setProjectName}
          required
        />
      </Modal>
    </Box>
  );
};
```

## Best Practices

1. **Accessibilité** : Tous les composants incluent les attributs ARIA nécessaires
2. **Performance** : Utilisation de React.memo et useMemo pour optimiser les rendus
3. **Testabilité** : Attributs data-testid pour les tests automatisés
4. **Réutilisabilité** : Props flexibles et composition plutôt qu'héritage
5. **Cohérence** : Utilisation du système de design Material-UI

## Export Central

```typescript
// components/shared/index.ts
export * from './Button';
export * from './Card';
export * from './Input';
export * from './Modal';
export * from './Table';
export * from './Notification';
export * from './Loading';
```