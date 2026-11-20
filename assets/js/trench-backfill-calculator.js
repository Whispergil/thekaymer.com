/* Findry Trench Backfill Calculator.
   Backfill volume = trench volume (length × width × depth) minus the volume of an
   optional round pipe (π × (diameter ÷ 2)² × length). Material weights reuse the
   Material Calculator densities (window.FindryMaterialCalculator) so both tools
   agree. Trips are volume ÷ truck capacity, rounded up. There is no waste,
   swell, or compaction allowance. */
(function (root, factory) {
  var shared = (typeof module === 'object' && module.exports)
    ? require('./material-calculator.js')
    : root.FindryMaterialCalculator;
  var api = factory(shared);
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.FindryTrenchBackfillCalculator = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (shared) {
  'use strict';

  if (!shared) return null;

  var DENSITY = shared.MATERIAL_DENSITY_US_SHORT_TONS_PER_CUBIC_YARD;
  var MATERIALS = shared.MATERIALS;
  var CUBIC_FEET_PER_CUBIC_YARD = shared.CUBIC_FEET_PER_CUBIC_YARD;
  var CUBIC_FEET_PER_CUBIC_METER = shared.CUBIC_FEET_PER_CUBIC_METER;
  var US_SHORT_TON_TO_METRIC_TONNE = shared.US_SHORT_TON_TO_METRIC_TONNE;
  var DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS = shared.DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS;
  var parsePositiveFiniteNumber = shared.parsePositiveFiniteNumber;
  var getDimensionError = shared.getDimensionError;
  var getCustomYardCapacityError = shared.getCustomYardCapacityError;
  var formatEstimate = shared.formatEstimate;
  var formatTrips = shared.formatTrips;

  var CAPACITY_UNITS = shared.MATERIAL_TRUCK_CAPACITY_UNITS;
  var SAFETY_TEXT = 'Estimates only. Actual quantities and weight vary by moisture, compaction, ' +
    'material source, bedding, and hauling limits. Confirm density, order quantity, compaction ' +
    'requirements, and safe payload with your supplier, engineer, or hauler.';
  var DIMENSION_FIELDS = Object.freeze({
    imperial: Object.freeze([
      Object.freeze({ key: 'length', label: 'Trench length', unit: 'ft', placeholder: 'e.g. 100' }),
      Object.freeze({ key: 'width', label: 'Trench width', unit: 'ft', placeholder: 'e.g. 2' }),
      Object.freeze({ key: 'depth', label: 'Trench depth', unit: 'ft', placeholder: 'e.g. 4' }),
      Object.freeze({ key: 'pipe', label: 'Pipe diameter', unit: 'in', placeholder: 'e.g. 6' }),
    ]),
    metric: Object.freeze([
      Object.freeze({ key: 'length', label: 'Trench length', unit: 'm', placeholder: 'e.g. 30' }),
      Object.freeze({ key: 'width', label: 'Trench width', unit: 'm', placeholder: 'e.g. 0.6' }),
      Object.freeze({ key: 'depth', label: 'Trench depth', unit: 'm', placeholder: 'e.g. 1.2' }),
      Object.freeze({ key: 'pipe', label: 'Pipe diameter', unit: 'mm', placeholder: 'e.g. 150' }),
    ]),
  });

  function isBlank(value) {
    return value === undefined || value === null || String(value).trim().length === 0;
  }

  // Optional field: blank means no pipe. Otherwise it must be a positive number
  // that fits inside the trench cross-section.
  function getPipeError(value, widthValue, depthValue, unitSystem) {
    if (isBlank(value)) return '';
    var diameter = parsePositiveFiniteNumber(String(value));
    if (diameter === null) return 'Use a number greater than 0, or leave it blank.';
    var width = parsePositiveFiniteNumber(String(widthValue));
    var depth = parsePositiveFiniteNumber(String(depthValue));
    if (width === null || depth === null) return '';
    var diameterInTrenchUnits = unitSystem === 'imperial' ? diameter / 12 : diameter / 1000;
    if (diameterInTrenchUnits >= width || diameterInTrenchUnits >= depth) {
      return 'The pipe must be smaller than the trench width and depth.';
    }
    return '';
  }

  // Whole trips: round the load equivalent up. A tiny tolerance stops float
  // noise (for example 3.0000000000000004) from adding a phantom trip.
  function roundUpTrips(loadEquivalent) {
    if (!Number.isFinite(loadEquivalent) || loadEquivalent <= 0) return null;
    var trips = Math.ceil(loadEquivalent - 1e-9);
    if (trips < 1) trips = 1;
    return Number.isSafeInteger(trips) ? trips : null;
  }

  function calculateTrenchBackfill(input) {
    input = input || {};
    var unitSystem = input.unitSystem;
    var material = input.material;
    if (unitSystem !== 'imperial' && unitSystem !== 'metric') return null;
    if (typeof material !== 'string' || !Object.prototype.hasOwnProperty.call(DENSITY, material)) return null;

    var length = parsePositiveFiniteNumber(input.length);
    var width = parsePositiveFiniteNumber(input.width);
    var depth = parsePositiveFiniteNumber(input.depth);
    if (length === null || width === null || depth === null) return null;

    var pipeDiameter = 0;
    if (!isBlank(input.pipeDiameter)) {
      pipeDiameter = parsePositiveFiniteNumber(input.pipeDiameter);
      if (pipeDiameter === null) return null;
    }

    var capacityUnit = input.truckCapacityUnit === undefined
      ? CAPACITY_UNITS.CUBIC_YARDS : input.truckCapacityUnit;
    if (capacityUnit !== CAPACITY_UNITS.CUBIC_YARDS && capacityUnit !== CAPACITY_UNITS.CUBIC_METRES) return null;
    var capacity = parsePositiveFiniteNumber(
      input.truckCapacity === undefined && capacityUnit === CAPACITY_UNITS.CUBIC_YARDS
        ? DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS : input.truckCapacity);
    if (capacity === null) return null;

    // Pipe diameter is in inches (Imperial) or millimetres (Metric).
    var diameter = unitSystem === 'imperial' ? pipeDiameter / 12 : pipeDiameter / 1000;
    if (diameter >= width || diameter >= depth) return null;

    var trenchVolume = length * width * depth;              // ft³ or m³
    var pipeVolume = Math.PI * Math.pow(diameter / 2, 2) * length;
    var backfillVolume = trenchVolume - pipeVolume;

    var toCubicFeet = unitSystem === 'imperial' ? 1 : CUBIC_FEET_PER_CUBIC_METER;
    var trenchCubicFeet = trenchVolume * toCubicFeet;
    var pipeCubicFeet = pipeVolume * toCubicFeet;
    var cubicFeet = backfillVolume * toCubicFeet;
    var cubicYards = cubicFeet / CUBIC_FEET_PER_CUBIC_YARD;
    var cubicMeters = cubicFeet / CUBIC_FEET_PER_CUBIC_METER;
    var estimatedUsShortTons = cubicYards * DENSITY[material];
    var estimatedMetricTonnes = estimatedUsShortTons * US_SHORT_TON_TO_METRIC_TONNE;

    var loadVolume = capacityUnit === CAPACITY_UNITS.CUBIC_YARDS ? cubicYards : cubicMeters;
    var exactLoadEquivalent = loadVolume / capacity;
    var estimatedTripsByVolume = roundUpTrips(exactLoadEquivalent);

    var values = [cubicFeet, cubicYards, cubicMeters, estimatedUsShortTons, estimatedMetricTonnes, exactLoadEquivalent];
    if (values.some(function (v) { return !Number.isFinite(v) || v <= 0 || v > Number.MAX_SAFE_INTEGER; }) ||
        estimatedTripsByVolume === null) return null;

    return {
      trenchCubicYards: trenchCubicFeet / CUBIC_FEET_PER_CUBIC_YARD,
      trenchCubicMeters: trenchCubicFeet / CUBIC_FEET_PER_CUBIC_METER,
      pipeCubicYards: pipeCubicFeet / CUBIC_FEET_PER_CUBIC_YARD,
      pipeCubicMeters: pipeCubicFeet / CUBIC_FEET_PER_CUBIC_METER,
      cubicFeet: cubicFeet,
      cubicYards: cubicYards,
      cubicMeters: cubicMeters,
      estimatedUsShortTons: estimatedUsShortTons,
      estimatedMetricTonnes: estimatedMetricTonnes,
      truckCapacity: capacity,
      truckCapacityUnit: capacityUnit,
      exactLoadEquivalent: exactLoadEquivalent,
      estimatedTripsByVolume: estimatedTripsByVolume,
    };
  }

  function formatLoads(value) {
    if (!Number.isFinite(value) || value <= 0) return '';
    if (value < 0.01) return '<0.01 loads';
    return value.toLocaleString('en-US', { maximumFractionDigits: 2 }) + ' loads';
  }

  function formatMass(value, unit) {
    if (!Number.isFinite(value) || value <= 0) return '';
    var formatted = value < 0.01 ? '<0.01' : value.toLocaleString('en-US', { maximumFractionDigits: 2 });
    return formatted + ' ' + (unit === 'metric-tonnes' ? 'metric tonnes' : 'US short tons');
  }

  function materialLabel(key) {
    for (var i = 0; i < MATERIALS.length; i += 1) {
      if (MATERIALS[i].key === key) return MATERIALS[i].label;
    }
    return key;
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function init(rootEl) {
    if (!rootEl) return null;
    var q = function (sel) { return rootEl.querySelector(sel); };

    var form = q('[data-trench-form]');
    var materialSelect = q('#trench-calc-material');
    var capacitySelect = q('#trench-calc-capacity-preset');
    var capacityInput = q('#trench-calc-capacity');
    var capacityEntryWrap = q('[data-capacity-entry]');
    var capacityEntryLabel = q('[data-capacity-entry-label]');
    var capacityEntryUnit = q('[data-capacity-entry-unit]');
    var capacityHint = q('[data-capacity-hint]');
    var capacityPresets = q('[data-capacity-presets]');
    var capacityError = q('#trench-calc-capacity-error');
    var results = q('[data-trench-results]');
    var status = q('[data-trench-status]');
    var unitInputs = rootEl.querySelectorAll('input[name="trench-calc-units"]');
    var capacityUnitInputs = rootEl.querySelectorAll('input[name="trench-calc-capacity-unit"]');

    var fieldMap = {};
    ['length', 'width', 'depth', 'pipe'].forEach(function (key) {
      fieldMap[key] = {
        input: q('#trench-calc-' + key),
        error: q('#trench-calc-' + key + '-error'),
        unit: q('[data-' + key + '-unit]'),
      };
    });

    var state = {
      material: materialSelect ? materialSelect.value : 'gravel',
      unitSystem: 'imperial',
      capacityUnit: CAPACITY_UNITS.CUBIC_YARDS,
      truckCapacity: DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS,
      usingCustomYards: false,
    };

    function syncDimensionLabels() {
      DIMENSION_FIELDS[state.unitSystem].forEach(function (field) {
        var map = fieldMap[field.key];
        if (map.unit) map.unit.textContent = field.unit;
        if (map.input) map.input.setAttribute('placeholder', field.placeholder);
      });
    }

    function showCapacityControls() {
      var yards = state.capacityUnit === CAPACITY_UNITS.CUBIC_YARDS;
      if (capacityPresets) capacityPresets.hidden = !yards;
      if (!yards) {
        capacityEntryWrap.hidden = false;
        capacityEntryLabel.textContent = 'Capacity';
        capacityEntryUnit.textContent = 'm³';
        capacityHint.hidden = false;
        capacityInput.setAttribute('placeholder', 'e.g. 7.6');
        capacityInput.setAttribute('aria-label', 'Your truck capacity in cubic metres');
        return;
      }
      capacityHint.hidden = true;
      capacityEntryLabel.textContent = 'Custom truck capacity (yd³)';
      capacityEntryUnit.textContent = 'yd³';
      capacityInput.setAttribute('placeholder', 'e.g. 24');
      capacityInput.setAttribute('aria-label', 'Custom truck capacity in cubic yards');
      if (state.usingCustomYards) {
        capacityEntryWrap.hidden = false;
        capacitySelect.value = 'custom';
      } else {
        capacityEntryWrap.hidden = true;
        capacitySelect.value = String(state.truckCapacity);
        capacityInput.value = '';
      }
    }

    function clearFieldError(key) {
      var map = fieldMap[key];
      if (map.error) map.error.textContent = '';
      if (map.input) map.input.removeAttribute('aria-invalid');
    }

    function clearErrorsAndResults() {
      Object.keys(fieldMap).forEach(clearFieldError);
      capacityError.textContent = '';
      capacityInput.removeAttribute('aria-invalid');
      capacitySelect.removeAttribute('aria-invalid');
      results.hidden = true;
      if (status) status.textContent = '';
    }

    function clearMeasurements() {
      Object.keys(fieldMap).forEach(function (key) { fieldMap[key].input.value = ''; });
    }

    function setUnitSystem(next, options) {
      var previous = state.unitSystem;
      state.unitSystem = next;
      unitInputs.forEach(function (input) { input.checked = input.value === next; });
      syncDimensionLabels();
      if (!(options && options.silent) && previous !== next) {
        clearMeasurements();
        clearErrorsAndResults();
      }
    }

    function setCapacityUnit(next, options) {
      var previous = state.capacityUnit;
      state.capacityUnit = next;
      capacityUnitInputs.forEach(function (input) { input.checked = input.value === next; });
      if (!(options && options.silent) && previous !== next) {
        state.truckCapacity = DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS;
        state.usingCustomYards = false;
        capacityInput.value = '';
        clearErrorsAndResults();
      }
      showCapacityControls();
    }

    // Same as the other Findry calculators: Reset clears the measurements and
    // the result, but keeps material, units, and truck capacity.
    function startNewCalculation() {
      clearMeasurements();
      clearErrorsAndResults();
      fieldMap.length.input.focus();
    }

    function capacityValue() {
      if (state.capacityUnit === CAPACITY_UNITS.CUBIC_YARDS && !state.usingCustomYards) {
        return String(state.truckCapacity);
      }
      return capacityInput.value;
    }

    function setText(sel, text) {
      var el = q(sel);
      if (el) el.textContent = text;
    }

    function calculate(event) {
      if (event) event.preventDefault();
      var v = {};
      Object.keys(fieldMap).forEach(function (key) { v[key] = fieldMap[key].input.value; });

      var errors = {
        length: getDimensionError(v.length),
        width: getDimensionError(v.width),
        depth: getDimensionError(v.depth),
        pipe: getPipeError(v.pipe, v.width, v.depth, state.unitSystem),
      };
      var capacityMsg = '';
      if (state.capacityUnit === CAPACITY_UNITS.CUBIC_METRES) {
        capacityMsg = getDimensionError(capacityInput.value);
      } else if (state.usingCustomYards) {
        capacityMsg = getCustomYardCapacityError(capacityInput.value);
      }

      Object.keys(errors).forEach(function (key) {
        fieldMap[key].error.textContent = errors[key];
        fieldMap[key].input.setAttribute('aria-invalid', errors[key] ? 'true' : 'false');
      });
      capacityError.textContent = capacityMsg;
      var capacityTarget = (state.capacityUnit === CAPACITY_UNITS.CUBIC_YARDS && !state.usingCustomYards)
        ? capacitySelect : capacityInput;
      capacityTarget.setAttribute('aria-invalid', capacityMsg ? 'true' : 'false');

      var hasError = Object.keys(errors).some(function (key) { return Boolean(errors[key]); });
      if (hasError || capacityMsg) {
        results.hidden = true;
        if (status) status.textContent = '';
        return null;
      }

      var result = calculateTrenchBackfill({
        material: state.material,
        unitSystem: state.unitSystem,
        length: v.length,
        width: v.width,
        depth: v.depth,
        pipeDiameter: v.pipe,
        truckCapacityUnit: state.capacityUnit,
        truckCapacity: capacityValue(),
      });
      if (!result) {
        results.hidden = true;
        if (status) status.textContent = 'Unable to display this estimate safely. Check measurements and capacity.';
        return null;
      }

      var metric = state.unitSystem === 'metric';
      var capacityLabel = result.truckCapacity + (state.capacityUnit === CAPACITY_UNITS.CUBIC_YARDS ? ' yd³' : ' m³');
      var hasPipe = !isBlank(v.pipe);
      setText('[data-result-context]', materialLabel(state.material) + ' · ' +
        (metric ? 'Metric' : 'Imperial') + ' measurements · Truck Capacity: ' + capacityLabel);
      setText('[data-result-hero-label]', metric ? 'Backfill (cubic metres)' : 'Backfill (cubic yards)');
      setText('[data-result-hero]', metric
        ? formatEstimate(result.cubicMeters) + ' m³'
        : formatEstimate(result.cubicYards) + ' yd³');
      setText('[data-result-secondary-label]', metric ? 'Backfill (cubic yards)' : 'Backfill (cubic metres)');
      setText('[data-result-secondary]', metric
        ? formatEstimate(result.cubicYards) + ' yd³'
        : formatEstimate(result.cubicMeters) + ' m³');
      setText('[data-result-trench]', metric
        ? formatEstimate(result.trenchCubicMeters) + ' m³'
        : formatEstimate(result.trenchCubicYards) + ' yd³');
      var pipeRow = q('[data-result-pipe-row]');
      if (pipeRow) pipeRow.hidden = !hasPipe;
      setText('[data-result-pipe]', hasPipe
        ? '− ' + (metric ? formatEstimate(result.pipeCubicMeters) + ' m³' : formatEstimate(result.pipeCubicYards) + ' yd³')
        : '');
      setText('[data-result-mass-label]', metric ? 'Estimated Metric Tonnes' : 'Estimated US Short Tons');
      setText('[data-result-mass]', metric
        ? formatMass(result.estimatedMetricTonnes, 'metric-tonnes')
        : formatMass(result.estimatedUsShortTons, 'us-short-tons'));
      setText('[data-result-loads]', formatLoads(result.exactLoadEquivalent));
      setText('[data-result-trips]', formatTrips(result.estimatedTripsByVolume));

      var measurements = q('[data-result-measurements]');
      if (measurements) {
        measurements.innerHTML = DIMENSION_FIELDS[state.unitSystem].filter(function (field) {
          return field.key !== 'pipe' || hasPipe;
        }).map(function (field) {
          return '<div><dt>' + field.label + '</dt><dd>' + escapeHtml(v[field.key].trim()) + ' ' + field.unit + '</dd></div>';
        }).join('');
      }
      setText('[data-result-safety]', SAFETY_TEXT);
      results.hidden = false;
      if (status) status.textContent = '';
      return result;
    }

    if (materialSelect) {
      materialSelect.addEventListener('change', function () {
        state.material = materialSelect.value;
        clearErrorsAndResults();
      });
    }
    unitInputs.forEach(function (input) {
      input.addEventListener('change', function () { setUnitSystem(input.value); });
    });
    capacityUnitInputs.forEach(function (input) {
      input.addEventListener('change', function () { setCapacityUnit(input.value); });
    });
    capacitySelect.addEventListener('change', function () {
      if (capacitySelect.value === 'custom') {
        state.usingCustomYards = true;
        capacityEntryWrap.hidden = false;
        capacityInput.value = '';
        capacityInput.focus();
      } else {
        state.usingCustomYards = false;
        state.truckCapacity = Number(capacitySelect.value);
        capacityEntryWrap.hidden = true;
        capacityInput.value = '';
      }
      clearErrorsAndResults();
    });
    Object.keys(fieldMap).forEach(function (key) {
      fieldMap[key].input.addEventListener('input', function () {
        if (results.hidden === false || fieldMap[key].error.textContent) {
          clearFieldError(key);
          results.hidden = true;
        }
      });
    });
    capacityInput.addEventListener('input', function () {
      if (results.hidden === false || capacityError.textContent) {
        capacityError.textContent = '';
        capacityInput.removeAttribute('aria-invalid');
        capacitySelect.removeAttribute('aria-invalid');
        results.hidden = true;
      }
    });
    form.addEventListener('submit', calculate);
    Array.prototype.forEach.call(rootEl.querySelectorAll('[data-trench-reset]'), function (button) {
      button.addEventListener('click', function (event) {
        event.preventDefault();
        startNewCalculation();
      });
    });
    var editButton = q('[data-trench-edit]');
    if (editButton) {
      editButton.addEventListener('click', function (event) {
        event.preventDefault();
        fieldMap.length.input.focus();
      });
    }

    form.removeAttribute('hidden');
    setUnitSystem('imperial', { silent: true });
    setCapacityUnit(CAPACITY_UNITS.CUBIC_YARDS, { silent: true });

    return {
      calculate: calculate,
      startNewCalculation: startNewCalculation,
      getState: function () { return state; },
    };
  }

  function autoInit() {
    var rootEl = typeof document !== 'undefined' && document.getElementById('trench-calc');
    if (rootEl) init(rootEl);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', autoInit);
    } else {
      autoInit();
    }
  }

  return {
    calculateTrenchBackfill: calculateTrenchBackfill,
    getPipeError: getPipeError,
    roundUpTrips: roundUpTrips,
    formatLoads: formatLoads,
    init: init,
  };
});
