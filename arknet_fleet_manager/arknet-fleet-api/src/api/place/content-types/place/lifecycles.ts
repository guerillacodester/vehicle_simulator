export default {
  /**
   * Cascade delete: When a country is deleted, this is called automatically
   * via the relation cleanup
   */
  async beforeDeleteMany(event: any) {
    const { where } = event.params;
    
    if (where.country) {
      const countryId = where.country;
      console.log(`[Place] Cleaning up places for country ${countryId}`);
    }
  }
};
