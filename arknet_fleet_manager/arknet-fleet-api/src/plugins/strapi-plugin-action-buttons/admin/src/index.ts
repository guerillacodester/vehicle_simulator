export default {
  register(app: any) {
    // Register the custom field
    app.customFields.register({
      name: 'action-button',
      pluginId: 'action-buttons',
      type: 'json',
      intlLabel: {
        id: 'action-buttons.button-field.label',
        defaultMessage: 'Action Button',
      },
      intlDescription: {
        id: 'action-buttons.button-field.description',
        defaultMessage: 'Production-ready action button field with configurable handlers',
      },
      icon: () => null,
      components: {
        Input: async () => import('./components/CustomFieldButton'),
      },
      options: {
        base: [],
        advanced: [
          {
            sectionTitle: {
              id: 'action-buttons.button-field.section.configuration',
              defaultMessage: 'Button Configuration',
            },
            items: [
              {
                name: 'options.buttonLabel',
                type: 'text',
                intlLabel: {
                  id: 'action-buttons.button-field.buttonLabel.label',
                  defaultMessage: 'Button Label',
                },
                description: {
                  id: 'action-buttons.button-field.buttonLabel.description',
                  defaultMessage: 'The text displayed on the button (e.g., "Send Email", "Upload Data")',
                },
                placeholder: {
                  id: 'action-buttons.button-field.buttonLabel.placeholder',
                  defaultMessage: 'Execute Action',
                },
              },
              {
                name: 'options.onClick',
                type: 'text',
                intlLabel: {
                  id: 'action-buttons.button-field.onClick.label',
                  defaultMessage: 'Handler Function',
                },
                description: {
                  id: 'action-buttons.button-field.onClick.description',
                  defaultMessage: 'The name of the window function to call (e.g., "handleSendEmail")',
                },
                placeholder: {
                  id: 'action-buttons.button-field.onClick.placeholder',
                  defaultMessage: 'handleDefaultAction',
                },
              },
            ],
          },
        ],
        validator: () => ({}),
      },
    });
  },
  
  bootstrap(app: any) {
    // Plugin bootstrap logic if needed
  },
};
