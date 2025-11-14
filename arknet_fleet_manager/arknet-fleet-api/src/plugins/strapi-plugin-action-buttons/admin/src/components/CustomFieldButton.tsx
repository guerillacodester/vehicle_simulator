import React from 'react';
import { Button } from '@strapi/design-system';
import { Play } from '@strapi/icons';

interface CustomFieldButtonProps {
  name: string;
  value?: any;
  onChange?: (value: any) => void;
  disabled?: boolean;
  attribute?: {
    options?: {
      buttonLabel?: string;
      onClick?: string;
    };
  };
}

const CustomFieldButton: React.FC<CustomFieldButtonProps> = ({ 
  name, 
  value, 
  onChange, 
  disabled, 
  attribute 
}) => {
  const buttonLabel = attribute?.options?.buttonLabel || 'Execute Action';
  const handlerName = attribute?.options?.onClick;

  const handleClick = () => {
    console.log('Button clicked!', name, value);
    
    // Call custom handler if provided via window global
    if (handlerName) {
      const globalHandler = (window as any)[handlerName];
      if (typeof globalHandler === 'function') {
        try {
          globalHandler(name, value, onChange);
          return;
        } catch (error) {
          console.error(`Error calling handler ${handlerName}:`, error);
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          alert(`Error: ${errorMessage}`);
          return;
        }
      }
    }
    
    // Default behavior
    alert(`Button "${name}" clicked!`);
    
    // Update the field value
    if (onChange) {
      onChange({ 
        lastClicked: new Date().toISOString(),
        clickCount: (value?.clickCount || 0) + 1 
      });
    }
  };

  return (
    <div>
      <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600 }}>
        {name}
      </label>
      <Button
        onClick={handleClick}
        startIcon={<Play />}
        variant="secondary"
        disabled={disabled}
        type="button"
      >
        {buttonLabel}
      </Button>
      {value?.lastClicked && (
        <div style={{ fontSize: '12px', marginTop: '8px', color: '#666' }}>
          Last: {new Date(value.lastClicked).toLocaleString()} ({value.clickCount}x)
        </div>
      )}
    </div>
  );
};

export default CustomFieldButton;
