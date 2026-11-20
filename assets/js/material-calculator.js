/* Findry Material Calculator — same math as the Findry 1.0.2 app.
   Volume comes from length, width, and depth. Density estimates weight only.
   Trips are volume ÷ truck capacity. There is no waste or compaction allowance. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.FindryMaterialCalculator = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var MATERIALS = Object.freeze([
    Object.freeze({ key: 'gravel', label: 'Gravel' }),
    Object.freeze({ key: 'crushed-stone', label: 'Crushed Stone' }),
    Object.freeze({ key: 'sand', label: 'Sand' }),
    Object.freeze({ key: 'topsoil', label: 'Topsoil' }),
    Object.freeze({ key: 'fill-dirt', label: 'Fill Dirt' }),
    Object.freeze({ key: 'mulch', label: 'Mulch' }),
    Object.freeze({ key: 'concrete', label: 'Concrete' }),
    Object.freeze({ key: 'asphalt-millings', label: 'Asphalt Millings' }),
  ]);

  var MATERIAL_DENSITY_US_SHORT_TONS_PER_CUBIC_YARD = Object.freeze({
    gravel: 1.4,
    'crushed-stone': 1.5,
    sand: 1.35,
    topsoil: 1.1,
    'fill-dirt': 1.2,
    mulch: 0.35,
    concrete: 2,
    'asphalt-millings': 1.35,
  });

  var DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS = 10;
  var YARD_PRESETS = Object.freeze([5, 6, 8, 10, 12, 14, 16, 18, 20]);
  var CUBIC_FEET_PER_CUBIC_YARD = 27;
  var CUBIC_FEET_PER_CUBIC_METER = 35.314666721;
  var US_SHORT_TON_TO_METRIC_TONNE = 0.90718474;
  var WEIGHT_UNIT_LABEL = 'US short tons';
  var VALID_UNIT_SYSTEMS = { imperial: true, metric: true };
  var MATERIAL_TRUCK_CAPACITY_UNITS = Object.freeze({
    CUBIC_YARDS: 'cubic-yards',
    CUBIC_METRES: 'cubic-metres',
  });
  var UNIT_LABELS = Object.freeze({
    'cubic-yards': { name: 'Cubic Yards', symbol: 'yd³' },
    'cubic-metres': { name: 'Cubic Metres', symbol: 'm³' },
    'us-short-tons': { name: 'US Short Tons', symbol: 'US short tons' },
    'metric-tonnes': { name: 'Metric Tonnes', symbol: 't' },
  });
  var MATERIAL_ESTIMATE_SAFETY_TEXT = 'Estimates only. Actual quantities and weight vary by moisture, compaction, material source, and hauling limits. Confirm density, order quantity, and safe payload with your supplier or hauler.';
  var DIMENSION_FIELDS = Object.freeze({
    imperial: Object.freeze([
      Object.freeze({ key: 'length', label: 'Length', unit: 'ft', placeholder: 'e.g. 40' }),
      Object.freeze({ key: 'width', label: 'Width', unit: 'ft', placeholder: 'e.g. 20' }),
      Object.freeze({ key: 'depth', label: 'Depth', unit: 'in', placeholder: 'e.g. 6' }),
    ]),
    metric: Object.freeze([
      Object.freeze({ key: 'length', label: 'Length', unit: 'm', placeholder: 'e.g. 12' }),
      Object.freeze({ key: 'width', label: 'Width', unit: 'm', placeholder: 'e.g. 6' }),
      Object.freeze({ key: 'depth', label: 'Depth', unit: 'cm', placeholder: 'e.g. 15' }),
    ]),
  });

  function parsePositiveFiniteNumber(rawValue) {
    if (typeof rawValue !== 'string' && typeof rawValue !== 'number') return null;
    if (typeof rawValue === 'string' && rawValue.trim().length === 0) return null;
    var parsed = typeof rawValue === 'number' ? rawValue : Number(rawValue.trim());
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }

  function isValidMaterialKey(material) {
    return typeof material === 'string' &&
      Object.prototype.hasOwnProperty.call(MATERIAL_DENSITY_US_SHORT_TONS_PER_CUBIC_YARD, material);
  }

  function isValidUnitSystem(unitSystem) {
    return Boolean(VALID_UNIT_SYSTEMS[unitSystem]);
  }

  function getDimensionError(value) {
    if (typeof value !== 'string' || value.trim().length === 0) return 'Required.';
    return parsePositiveFiniteNumber(value) === null ? 'Use a number greater than 0.' : '';
  }

  function getCustomYardCapacityError(value) {
    if (parsePositiveFiniteNumber(value) === null) return 'Enter a capacity greater than 0.';
    return '';
  }

  function decimalFactor(value) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return null;
    var match = String(value).match(/^(\d+)(?:\.(\d+))?(?:e([+-]?\d+))?$/i);
    if (!match) return null;
    return {
      digits: BigInt(match[1] + (match[2] || '')),
      exponent: Number(match[3] || 0) - (match[2] ? match[2].length : 0),
    };
  }

  function calculateDecimalTripCount(numeratorFactors, denominatorFactors) {
    if (!Array.isArray(numeratorFactors) || numeratorFactors.length === 0 ||
        !Array.isArray(denominatorFactors) || denominatorFactors.length === 0) return null;

    var numerator = 1n;
    var denominator = 1n;
    var exponent = 0;
    var i;
    var factor;
    for (i = 0; i < numeratorFactors.length; i += 1) {
      factor = decimalFactor(numeratorFactors[i]);
      if (!factor) return null;
      numerator *= factor.digits;
      exponent += factor.exponent;
    }
    for (i = 0; i < denominatorFactors.length; i += 1) {
      factor = decimalFactor(denominatorFactors[i]);
      if (!factor) return null;
      denominator *= factor.digits;
      exponent -= factor.exponent;
    }
    if (exponent > 0) numerator *= 10n ** BigInt(exponent);
    if (exponent < 0) denominator *= 10n ** BigInt(-exponent);

    var trips = (numerator + denominator - 1n) / denominator;
    return trips > BigInt(Number.MAX_SAFE_INTEGER) ? null : Number(trips);
  }

  function calculateVolumeBasedLoadEquivalent(volume, capacity, tripFactors) {
    var parsedVolume = parsePositiveFiniteNumber(volume);
    var parsedCapacity = parsePositiveFiniteNumber(capacity);
    if (parsedVolume === null || parsedCapacity === null) return null;

    var exactLoadEquivalent = parsedVolume / parsedCapacity;
    if (!Number.isFinite(exactLoadEquivalent) || exactLoadEquivalent <= 0) return null;

    var estimatedTripsByVolume = calculateDecimalTripCount(
      (tripFactors && tripFactors.numerator) || [parsedVolume],
      (tripFactors && tripFactors.denominator) || [parsedCapacity]
    );
    if (estimatedTripsByVolume === null) return null;
    return {
      capacity: parsedCapacity,
      exactLoadEquivalent: exactLoadEquivalent,
      estimatedTripsByVolume: estimatedTripsByVolume,
    };
  }

  function calculateMaterialEstimate(input) {
    input = input || {};
    var material = input.material;
    var unitSystem = input.unitSystem;
    var length = input.length;
    var width = input.width;
    var depth = input.depth;
    var truckCapacityCubicYards = input.truckCapacityCubicYards;
    var truckCapacityCubicMeters = input.truckCapacityCubicMeters;
    var truckCapacityUnit = input.truckCapacityUnit === undefined
      ? MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS
      : input.truckCapacityUnit;

    if (!isValidMaterialKey(material) || !isValidUnitSystem(unitSystem)) return null;
    if (truckCapacityUnit !== MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS &&
        truckCapacityUnit !== MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_METRES) return null;
    if (truckCapacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS &&
        truckCapacityCubicMeters !== undefined) return null;
    if (truckCapacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_METRES &&
        truckCapacityCubicYards !== undefined) return null;

    var parsedLength = parsePositiveFiniteNumber(length);
    var parsedWidth = parsePositiveFiniteNumber(width);
    var parsedDepth = parsePositiveFiniteNumber(depth);
    if (parsedLength === null || parsedWidth === null || parsedDepth === null) return null;

    var cubicFeet;
    var cubicMeters;

    if (unitSystem === 'imperial') {
      cubicFeet = parsedLength * parsedWidth * (parsedDepth / 12);
      cubicMeters = cubicFeet / CUBIC_FEET_PER_CUBIC_METER;
    } else {
      cubicMeters = parsedLength * parsedWidth * (parsedDepth / 100);
      cubicFeet = cubicMeters * CUBIC_FEET_PER_CUBIC_METER;
    }

    var cubicYards = cubicFeet / CUBIC_FEET_PER_CUBIC_YARD;
    var estimatedUsShortTons = cubicYards * MATERIAL_DENSITY_US_SHORT_TONS_PER_CUBIC_YARD[material];
    var estimatedMetricTonnes = estimatedUsShortTons * US_SHORT_TON_TO_METRIC_TONNE;
    var usesCubicYards = truckCapacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS;
    var capacity = usesCubicYards
      ? truckCapacityCubicYards === undefined ? DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS : truckCapacityCubicYards
      : truckCapacityCubicMeters;
    var parsedCapacity = parsePositiveFiniteNumber(capacity);
    var dimensions = [parsedLength, parsedWidth, parsedDepth];
    var tripFactors = unitSystem === 'imperial'
      ? usesCubicYards
        ? { numerator: dimensions, denominator: [324, parsedCapacity] }
        : { numerator: dimensions, denominator: [12, CUBIC_FEET_PER_CUBIC_METER, parsedCapacity] }
      : usesCubicYards
        ? { numerator: dimensions.concat([CUBIC_FEET_PER_CUBIC_METER]), denominator: [100, 27, parsedCapacity] }
        : { numerator: dimensions, denominator: [100, parsedCapacity] };
    var truckLoads = usesCubicYards
      ? calculateVolumeBasedLoadEquivalent(cubicYards, capacity, tripFactors)
      : calculateVolumeBasedLoadEquivalent(cubicMeters, capacity, tripFactors);

    var calculatedValues = [cubicFeet, cubicYards, cubicMeters, estimatedUsShortTons, estimatedMetricTonnes];
    if (calculatedValues.some(function (value) {
      return !Number.isFinite(value) || value <= 0;
    }) || !truckLoads) return null;

    var result = {
      cubicFeet: cubicFeet,
      cubicYards: cubicYards,
      cubicMeters: cubicMeters,
      estimatedUsShortTons: estimatedUsShortTons,
      estimatedMetricTonnes: estimatedMetricTonnes,
      weightUnit: WEIGHT_UNIT_LABEL,
      exactLoadEquivalent: truckLoads.exactLoadEquivalent,
      estimatedTripsByVolume: truckLoads.estimatedTripsByVolume,
    };
    if (usesCubicYards) {
      result.truckCapacityCubicYards = truckLoads.capacity;
    } else {
      result.truckCapacityUnit = truckCapacityUnit;
      result.truckCapacityCubicMeters = truckLoads.capacity;
    }
    return result;
  }

  function isSafelyDisplayableEstimate(result) {
    if (!result || typeof result !== 'object') return false;
    var capacity = result.truckCapacityUnit === 'cubic-metres'
      ? result.truckCapacityCubicMeters
      : result.truckCapacityUnit === undefined || result.truckCapacityUnit === 'cubic-yards'
        ? result.truckCapacityCubicYards
        : null;
    var positiveValues = [
      result.cubicFeet, result.cubicYards, result.cubicMeters,
      result.estimatedUsShortTons, capacity,
      result.exactLoadEquivalent,
    ];
    if (result.estimatedMetricTonnes !== undefined) positiveValues.push(result.estimatedMetricTonnes);
    var capacityVolume = result.truckCapacityUnit === 'cubic-metres'
      ? result.cubicMeters : result.cubicYards;
    var decimalTrips = calculateDecimalTripCount([capacityVolume], [capacity]);
    var floatingPointBoundary = result.estimatedTripsByVolume < result.exactLoadEquivalent &&
      result.exactLoadEquivalent - result.estimatedTripsByVolume <=
        Number.EPSILON * Math.max(1, result.estimatedTripsByVolume);
    return positiveValues.every(function (value) {
      return typeof value === 'number' && Number.isFinite(value) &&
        value > 0 && value <= Number.MAX_SAFE_INTEGER;
    }) &&
      Number.isSafeInteger(result.estimatedTripsByVolume) &&
      result.estimatedTripsByVolume > 0 &&
      (floatingPointBoundary || result.estimatedTripsByVolume === decimalTrips ||
        result.estimatedTripsByVolume === Math.ceil(result.exactLoadEquivalent));
  }

  function formatEstimate(value, maximumFractionDigits) {
    if (maximumFractionDigits === undefined) maximumFractionDigits = 2;
    if (value > 0 && value < 0.01) return '<0.01';
    return value.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: maximumFractionDigits,
    });
  }

  function formatEstimatedMaterialMass(result, unit) {
    if (!result || ['us-short-tons', 'metric-tonnes'].indexOf(unit) === -1) return null;
    var value = unit === 'metric-tonnes'
      ? (result.estimatedMetricTonnes !== undefined && result.estimatedMetricTonnes !== null
        ? result.estimatedMetricTonnes
        : result.estimatedUsShortTons * US_SHORT_TON_TO_METRIC_TONNE)
      : result.estimatedUsShortTons;
    if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0 ||
        value > Number.MAX_SAFE_INTEGER) return null;
    var formatted = value < 0.01
      ? '<0.01'
      : value.toLocaleString('en-US', { maximumFractionDigits: 2 });
    return formatted + ' ' + (unit === 'metric-tonnes' ? 'metric tonnes' : 'US short tons');
  }

  function formatLoadEquivalent(value, estimatedTrips) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return null;
    if (value < 0.01) return '<0.01 loads';
    var formatted = value.toLocaleString('en-US', { maximumFractionDigits: 2 });
    var roundedInteger = Math.round(value);
    if (!Number.isInteger(value) && formatted === roundedInteger.toLocaleString('en-US')) {
      if (value > roundedInteger && estimatedTrips === roundedInteger) {
        return formatted + ' loads';
      }
      return (value > roundedInteger ? '>' : '<') + formatted + ' loads';
    }
    return formatted + ' loads';
  }

  function formatTrips(value) {
    return Number.isSafeInteger(value) && value > 0
      ? value.toLocaleString('en-US') + ' ' + (value === 1 ? 'trip' : 'trips')
      : '';
  }

  function materialLabel(key) {
    var i;
    for (i = 0; i < MATERIALS.length; i += 1) {
      if (MATERIALS[i].key === key) return MATERIALS[i].label;
    }
    return key;
  }

  function init(root) {
    if (!root) return;

    var form = root.querySelector('[data-material-form]');
    var materialSelect = root.querySelector('#material-calc-material');
    var lengthInput = root.querySelector('#material-calc-length');
    var widthInput = root.querySelector('#material-calc-width');
    var depthInput = root.querySelector('#material-calc-depth');
    var lengthUnit = root.querySelector('[data-length-unit]');
    var widthUnit = root.querySelector('[data-width-unit]');
    var depthUnit = root.querySelector('[data-depth-unit]');
    var lengthError = root.querySelector('#material-calc-length-error');
    var widthError = root.querySelector('#material-calc-width-error');
    var depthError = root.querySelector('#material-calc-depth-error');
    var capacityError = root.querySelector('#material-calc-capacity-error');
    var capacitySelect = root.querySelector('#material-calc-capacity-preset');
    var capacityInput = root.querySelector('#material-calc-capacity');
    var capacityEntryWrap = root.querySelector('[data-capacity-entry]');
    var capacityEntryLabel = root.querySelector('[data-capacity-entry-label]');
    var capacityEntryUnit = root.querySelector('[data-capacity-entry-unit]');
    var capacityHint = root.querySelector('[data-capacity-hint]');
    var capacityPresets = root.querySelector('[data-capacity-presets]');
    var results = root.querySelector('[data-material-results]');
    var resultsContext = root.querySelector('[data-result-context]');
    var resultsHeroLabel = root.querySelector('[data-result-hero-label]');
    var resultsHero = root.querySelector('[data-result-hero]');
    var resultsSecondaryLabel = root.querySelector('[data-result-secondary-label]');
    var resultsSecondary = root.querySelector('[data-result-secondary]');
    var resultsMassLabel = root.querySelector('[data-result-mass-label]');
    var resultsMass = root.querySelector('[data-result-mass]');
    var resultsLoads = root.querySelector('[data-result-loads]');
    var resultsTrips = root.querySelector('[data-result-trips]');
    var resultsMeasurements = root.querySelector('[data-result-measurements]');
    var resultsSafety = root.querySelector('[data-result-safety]');
    var status = root.querySelector('[data-material-status]');
    var unitInputs = root.querySelectorAll('input[name="material-calc-units"]');
    var capacityUnitInputs = root.querySelectorAll('input[name="material-calc-capacity-unit"]');

    var state = {
      material: 'gravel',
      unitSystem: 'imperial',
      capacityUnit: MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS,
      truckCapacity: DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS,
      usingCustomYards: false,
    };

    var fieldMap = {
      length: { input: lengthInput, error: lengthError, unit: lengthUnit },
      width: { input: widthInput, error: widthError, unit: widthUnit },
      depth: { input: depthInput, error: depthError, unit: depthUnit },
    };

    function syncDimensionLabels() {
      var fields = DIMENSION_FIELDS[state.unitSystem];
      fields.forEach(function (field) {
        var map = fieldMap[field.key];
        if (map.unit) map.unit.textContent = field.unit;
        if (map.input) map.input.setAttribute('placeholder', field.placeholder);
      });
    }

    function showCapacityControls() {
      var yards = state.capacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS;
      if (capacityPresets) capacityPresets.hidden = !yards;
      if (!yards) {
        if (capacityEntryWrap) capacityEntryWrap.hidden = false;
        if (capacityEntryLabel) capacityEntryLabel.textContent = 'Capacity';
        if (capacityEntryUnit) capacityEntryUnit.textContent = 'm³';
        if (capacityHint) {
          capacityHint.hidden = false;
          capacityHint.textContent = "Enter your truck's capacity in cubic metres.";
        }
        if (capacityInput) {
          capacityInput.setAttribute('placeholder', 'e.g. 12.5');
          capacityInput.setAttribute('maxlength', '16');
          capacityInput.setAttribute('aria-label', 'Your truck capacity in cubic metres');
        }
        return;
      }
      if (capacityHint) capacityHint.hidden = true;
      if (capacityEntryLabel) capacityEntryLabel.textContent = 'Custom truck capacity (yd³)';
      if (capacityEntryUnit) capacityEntryUnit.textContent = 'yd³';
      if (capacityInput) {
        capacityInput.setAttribute('placeholder', 'e.g. 24');
        capacityInput.setAttribute('maxlength', '12');
        capacityInput.setAttribute('aria-label', 'Custom truck capacity in cubic yards');
      }
      if (state.usingCustomYards) {
        if (capacityEntryWrap) capacityEntryWrap.hidden = false;
        if (capacitySelect) capacitySelect.value = 'custom';
      } else {
        if (capacityEntryWrap) capacityEntryWrap.hidden = true;
        if (capacitySelect) capacitySelect.value = String(state.truckCapacity);
        if (capacityInput) capacityInput.value = '';
      }
    }

    function clearFieldError(field) {
      var map = fieldMap[field];
      if (map && map.error) map.error.textContent = '';
      if (map && map.input) map.input.removeAttribute('aria-invalid');
    }

    function clearErrorsAndResults() {
      ['length', 'width', 'depth'].forEach(clearFieldError);
      if (capacityError) capacityError.textContent = '';
      if (capacityInput) capacityInput.removeAttribute('aria-invalid');
      if (capacitySelect) capacitySelect.removeAttribute('aria-invalid');
      if (results) results.hidden = true;
      if (status) status.textContent = '';
    }

    function setUnitSystem(nextUnitSystem, options) {
      var silent = options && options.silent;
      var previous = state.unitSystem;
      state.unitSystem = nextUnitSystem;
      unitInputs.forEach(function (input) {
        input.checked = input.value === nextUnitSystem;
      });
      syncDimensionLabels();
      if (!silent && previous !== nextUnitSystem) {
        lengthInput.value = '';
        widthInput.value = '';
        depthInput.value = '';
        clearErrorsAndResults();
      }
    }

    function setCapacityUnit(nextCapacityUnit, options) {
      var silent = options && options.silent;
      var previous = state.capacityUnit;
      state.capacityUnit = nextCapacityUnit;
      capacityUnitInputs.forEach(function (input) {
        input.checked = input.value === nextCapacityUnit;
      });
      if (!silent && previous !== nextCapacityUnit) {
        state.truckCapacity = DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS;
        state.usingCustomYards = false;
        if (capacityInput) capacityInput.value = '';
        clearErrorsAndResults();
      }
      showCapacityControls();
    }

    // Same as the app Reset / Start New Calculation: clear measurements and
    // the result, but keep material, dimension units, and truck capacity.
    function startNewCalculation() {
      lengthInput.value = '';
      widthInput.value = '';
      depthInput.value = '';
      clearErrorsAndResults();
      lengthInput.focus();
    }

    function capacityValue() {
      if (state.capacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS) {
        return state.usingCustomYards ? capacityInput.value : String(state.truckCapacity);
      }
      return capacityInput.value;
    }

    function calculate(event) {
      if (event) event.preventDefault();

      var dimensionErrors = {
        length: getDimensionError(lengthInput.value),
        width: getDimensionError(widthInput.value),
        depth: getDimensionError(depthInput.value),
      };
      var capacityMsg = '';
      if (state.capacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_METRES) {
        capacityMsg = getDimensionError(capacityInput.value);
      } else if (state.usingCustomYards) {
        capacityMsg = getCustomYardCapacityError(capacityInput.value);
      }

      Object.keys(dimensionErrors).forEach(function (key) {
        var map = fieldMap[key];
        var message = dimensionErrors[key];
        map.error.textContent = message;
        map.input.setAttribute('aria-invalid', message ? 'true' : 'false');
      });
      if (capacityError) capacityError.textContent = capacityMsg;
      if (state.capacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS && !state.usingCustomYards) {
        if (capacitySelect) capacitySelect.setAttribute('aria-invalid', capacityMsg ? 'true' : 'false');
        if (capacityInput) capacityInput.removeAttribute('aria-invalid');
      } else {
        if (capacityInput) capacityInput.setAttribute('aria-invalid', capacityMsg ? 'true' : 'false');
        if (capacitySelect) capacitySelect.removeAttribute('aria-invalid');
      }

      var hasDimensionError = Object.keys(dimensionErrors).some(function (key) {
        return Boolean(dimensionErrors[key]);
      });
      if (hasDimensionError || capacityMsg) {
        results.hidden = true;
        if (status) status.textContent = '';
        return null;
      }

      var estimateInput = {
        material: state.material,
        unitSystem: state.unitSystem,
        length: lengthInput.value,
        width: widthInput.value,
        depth: depthInput.value,
        truckCapacityUnit: state.capacityUnit,
      };
      if (state.capacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS) {
        estimateInput.truckCapacityCubicYards = capacityValue();
      } else {
        estimateInput.truckCapacityCubicMeters = capacityValue();
      }

      var result = calculateMaterialEstimate(estimateInput);
      if (!isSafelyDisplayableEstimate(result)) {
        results.hidden = true;
        if (status) {
          status.textContent = 'Unable to display this estimate safely. Check measurements and capacity.';
        }
        return null;
      }

      var primaryVolumeIsMetric = state.unitSystem === 'metric';
      var primaryMassUnit = primaryVolumeIsMetric ? 'metric-tonnes' : 'us-short-tons';
      var resultCapacityLabel = state.capacityUnit === MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS
        ? result.truckCapacityCubicYards + ' yd³'
        : result.truckCapacityCubicMeters + ' m³';
      var fields = DIMENSION_FIELDS[state.unitSystem];
      var measurements = {
        length: lengthInput.value,
        width: widthInput.value,
        depth: depthInput.value,
      };

      resultsContext.textContent =
        materialLabel(state.material) + ' · ' +
        (state.unitSystem === 'imperial' ? 'Imperial' : 'Metric') +
        ' measurements · Truck Capacity: ' + resultCapacityLabel;
      resultsHeroLabel.textContent = primaryVolumeIsMetric ? 'Cubic metres' : 'Cubic yards';
      resultsHero.textContent = primaryVolumeIsMetric
        ? formatEstimate(result.cubicMeters) + ' m³'
        : formatEstimate(result.cubicYards) + ' yd³';
      resultsSecondaryLabel.textContent = primaryVolumeIsMetric ? 'Cubic Yards' : 'Cubic Metres';
      resultsSecondary.textContent = primaryVolumeIsMetric
        ? formatEstimate(result.cubicYards) + ' yd³'
        : formatEstimate(result.cubicMeters) + ' m³';
      resultsMassLabel.textContent = 'Estimated ' + UNIT_LABELS[primaryMassUnit].name;
      resultsMass.textContent = formatEstimatedMaterialMass(result, primaryMassUnit) || '';
      resultsLoads.textContent = formatLoadEquivalent(result.exactLoadEquivalent, result.estimatedTripsByVolume) || '';
      resultsTrips.textContent = formatTrips(result.estimatedTripsByVolume);
      resultsMeasurements.innerHTML = fields.map(function (field) {
        return '<div><dt>' + field.label + '</dt><dd>' + measurements[field.key] + ' ' + field.unit + '</dd></div>';
      }).join('');
      resultsSafety.textContent = MATERIAL_ESTIMATE_SAFETY_TEXT;
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
      input.addEventListener('change', function () {
        setUnitSystem(input.value);
      });
    });
    capacityUnitInputs.forEach(function (input) {
      input.addEventListener('change', function () {
        setCapacityUnit(input.value);
      });
    });
    if (capacitySelect) {
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
    }
    ['length', 'width', 'depth'].forEach(function (key) {
      fieldMap[key].input.addEventListener('input', function () {
        if (results.hidden === false || fieldMap[key].error.textContent) {
          clearFieldError(key);
          results.hidden = true;
        }
      });
    });
    if (capacityInput) {
      capacityInput.addEventListener('input', function () {
        if (results.hidden === false || (capacityError && capacityError.textContent)) {
          if (capacityError) capacityError.textContent = '';
          capacityInput.removeAttribute('aria-invalid');
          if (capacitySelect) capacitySelect.removeAttribute('aria-invalid');
          results.hidden = true;
        }
      });
    }
    form.addEventListener('submit', calculate);
    var resetButtons = root.querySelectorAll('[data-material-reset]');
    Array.prototype.forEach.call(resetButtons, function (button) {
      button.addEventListener('click', function (event) {
        event.preventDefault();
        startNewCalculation();
      });
    });
    var editButton = root.querySelector('[data-material-edit]');
    if (editButton) {
      editButton.addEventListener('click', function (event) {
        event.preventDefault();
        lengthInput.focus();
      });
    }

    form.removeAttribute('hidden');
    setUnitSystem('imperial', { silent: true });
    setCapacityUnit(MATERIAL_TRUCK_CAPACITY_UNITS.CUBIC_YARDS, { silent: true });

    return {
      calculate: calculate,
      startNewCalculation: startNewCalculation,
      getState: function () { return state; },
    };
  }

  function autoInit() {
    var root = typeof document !== 'undefined' && document.getElementById('material-calc');
    if (root) init(root);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', autoInit);
    } else {
      autoInit();
    }
  }

  return {
    MATERIALS: MATERIALS,
    MATERIAL_DENSITY_US_SHORT_TONS_PER_CUBIC_YARD: MATERIAL_DENSITY_US_SHORT_TONS_PER_CUBIC_YARD,
    DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS: DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS,
    YARD_PRESETS: YARD_PRESETS,
    CUBIC_FEET_PER_CUBIC_YARD: CUBIC_FEET_PER_CUBIC_YARD,
    CUBIC_FEET_PER_CUBIC_METER: CUBIC_FEET_PER_CUBIC_METER,
    US_SHORT_TON_TO_METRIC_TONNE: US_SHORT_TON_TO_METRIC_TONNE,
    MATERIAL_TRUCK_CAPACITY_UNITS: MATERIAL_TRUCK_CAPACITY_UNITS,
    MATERIAL_ESTIMATE_SAFETY_TEXT: MATERIAL_ESTIMATE_SAFETY_TEXT,
    parsePositiveFiniteNumber: parsePositiveFiniteNumber,
    getDimensionError: getDimensionError,
    getCustomYardCapacityError: getCustomYardCapacityError,
    calculateDecimalTripCount: calculateDecimalTripCount,
    calculateMaterialEstimate: calculateMaterialEstimate,
    isSafelyDisplayableEstimate: isSafelyDisplayableEstimate,
    formatEstimate: formatEstimate,
    formatEstimatedMaterialMass: formatEstimatedMaterialMass,
    formatLoadEquivalent: formatLoadEquivalent,
    formatTrips: formatTrips,
    init: init,
  };
});
