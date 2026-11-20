/* Findry Truck Load Calculator — same math as the Findry 1.0.2 app.
   Quantity and capacity use one unit. There is no volume↔weight conversion. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.FindryTruckLoadCalculator = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var TRUCK_LOAD_UNITS = Object.freeze({
    CUBIC_YARDS: 'cubic-yards',
    CUBIC_METRES: 'cubic-metres',
    US_SHORT_TONS: 'us-short-tons',
    METRIC_TONNES: 'metric-tonnes',
  });
  var SUPPORTED_UNITS = {};
  Object.keys(TRUCK_LOAD_UNITS).forEach(function (key) {
    SUPPORTED_UNITS[TRUCK_LOAD_UNITS[key]] = true;
  });
  var VOLUME_UNITS = [TRUCK_LOAD_UNITS.CUBIC_YARDS, TRUCK_LOAD_UNITS.CUBIC_METRES];
  var YARD_PRESETS = Object.freeze([5, 6, 8, 10, 12, 14, 16, 18, 20]);
  var DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS = 10;

  var UNIT_LABELS = Object.freeze({
    'cubic-yards': { name: 'Cubic Yards', symbol: 'yd³' },
    'cubic-metres': { name: 'Cubic Metres', symbol: 'm³' },
    'us-short-tons': { name: 'US Short Tons', symbol: 'US short tons' },
    'metric-tonnes': { name: 'Metric Tonnes', symbol: 'metric tonnes' },
  });

  function isVolumeUnit(unit) {
    return unit === TRUCK_LOAD_UNITS.CUBIC_YARDS || unit === TRUCK_LOAD_UNITS.CUBIC_METRES;
  }

  function parsePositiveFiniteNumber(rawValue) {
    if (typeof rawValue !== 'string' && typeof rawValue !== 'number') return null;
    if (typeof rawValue === 'string' && rawValue.trim().length === 0) return null;
    var parsed = typeof rawValue === 'number' ? rawValue : Number(rawValue.trim());
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }

  function getInputError(value) {
    if (typeof value === 'string' && value.trim().length === 0) return 'Required.';
    if (value === '' || value == null) return 'Required.';
    var parsed = parsePositiveFiniteNumber(value);
    return parsed === null || parsed > Number.MAX_SAFE_INTEGER
      ? 'Enter a positive, finite number.'
      : '';
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

  function calculateTruckLoadEstimate(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) return null;
    var quantity = input.quantity;
    var capacity = input.capacity;
    var unitSystem = input.unitSystem;
    if (!SUPPORTED_UNITS[unitSystem]) return null;

    var parsedQuantity = parsePositiveFiniteNumber(quantity);
    var parsedCapacity = parsePositiveFiniteNumber(capacity);
    if (parsedQuantity === null || parsedCapacity === null ||
        parsedQuantity > Number.MAX_SAFE_INTEGER || parsedCapacity > Number.MAX_SAFE_INTEGER) {
      return null;
    }

    var exactLoadEquivalent = parsedQuantity / parsedCapacity;
    if (!Number.isFinite(exactLoadEquivalent) || exactLoadEquivalent <= 0 ||
        exactLoadEquivalent > Number.MAX_SAFE_INTEGER) return null;

    var estimatedTrips = calculateDecimalTripCount([parsedQuantity], [parsedCapacity]);
    if (!Number.isSafeInteger(estimatedTrips) || estimatedTrips <= 0) return null;

    return {
      quantity: parsedQuantity,
      capacity: parsedCapacity,
      unitSystem: unitSystem,
      exactLoadEquivalent: exactLoadEquivalent,
      estimatedTrips: estimatedTrips,
    };
  }

  function formatPositiveQuantity(value) {
    if (value < 0.01) return '<0.01';
    return value.toLocaleString('en-US', { maximumFractionDigits: 2 });
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

  function unitSymbol(unit) {
    return UNIT_LABELS[unit] ? UNIT_LABELS[unit].symbol : unit;
  }

  function loadEquivalentLabel(unit) {
    return isVolumeUnit(unit) ? 'Load Equivalent by Volume' : 'Load Equivalent by Weight Quantity';
  }

  function safetyText(unit) {
    if (isVolumeUnit(unit)) {
      return 'Volume-based estimate only. Actual hauling capacity depends on the vehicle, material, loading conditions, axle limits, route restrictions, and applicable laws.';
    }
    return "Weight-quantity estimate only. Findry does not determine legal payload, vehicle ratings, axle compliance, route restrictions, or safe hauling capacity. Confirm your truck's limits before hauling.";
  }

  function isYardPreset(value) {
    return YARD_PRESETS.indexOf(value) !== -1;
  }

  function init(root) {
    if (!root) return;

    var form = root.querySelector('[data-truck-form]');
    var quantityInput = root.querySelector('#truck-calc-quantity');
    var capacityInput = root.querySelector('#truck-calc-capacity');
    var capacitySelect = root.querySelector('#truck-calc-capacity-preset');
    var capacityCustomWrap = root.querySelector('[data-capacity-custom]');
    var presetWrap = root.querySelector('[data-capacity-presets]');
    var quantityError = root.querySelector('#truck-calc-quantity-error');
    var capacityError = root.querySelector('#truck-calc-capacity-error');
    var results = root.querySelector('[data-truck-results]');
    var resultsTrips = root.querySelector('[data-result-trips]');
    var resultsLoads = root.querySelector('[data-result-loads]');
    var resultsLoadsLabel = root.querySelector('[data-result-loads-label]');
    var resultsContext = root.querySelector('[data-result-context]');
    var resultsSafety = root.querySelector('[data-result-safety]');
    var status = root.querySelector('[data-truck-status]');
    var categoryInputs = root.querySelectorAll('input[name="truck-calc-category"]');
    var unitInputs = root.querySelectorAll('input[name="truck-calc-unit"]');
    var volumeUnits = root.querySelector('[data-units-volume]');
    var weightUnits = root.querySelector('[data-units-weight]');
    var quantityUnit = root.querySelector('[data-quantity-unit]');
    var capacityUnit = root.querySelector('[data-capacity-unit]');
    var capacityUnitCustom = root.querySelector('[data-capacity-unit-custom]');

    var state = {
      category: 'volume',
      unitSystem: TRUCK_LOAD_UNITS.CUBIC_YARDS,
      volumeCapacity: DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS,
      usingCustomYards: false,
    };

    function currentUnit() {
      return state.unitSystem;
    }

    function syncUnitLabels() {
      var symbol = unitSymbol(currentUnit());
      if (quantityUnit) quantityUnit.textContent = symbol;
      if (capacityUnit) capacityUnit.textContent = symbol;
      if (capacityUnitCustom) capacityUnitCustom.textContent = symbol;
      quantityInput.setAttribute('placeholder', isVolumeUnit(currentUnit()) ? 'e.g. 85' : 'e.g. 48');
      capacityInput.setAttribute('placeholder', currentUnit() === TRUCK_LOAD_UNITS.CUBIC_YARDS ? 'e.g. 24.5' : 'e.g. 24.5');
    }

    function showYardPresets(show) {
      if (presetWrap) presetWrap.hidden = !show;
      if (show) {
        if (state.usingCustomYards) {
          capacityCustomWrap.hidden = false;
          capacitySelect.value = 'custom';
          capacityInput.value = '';
        } else {
          capacityCustomWrap.hidden = true;
          capacitySelect.value = String(state.volumeCapacity);
          capacityInput.value = '';
        }
      } else {
        capacityCustomWrap.hidden = false;
        capacityInput.value = '';
      }
    }

    function setCategory(category, options) {
      var nextUnit = category === 'weight'
        ? TRUCK_LOAD_UNITS.US_SHORT_TONS
        : TRUCK_LOAD_UNITS.CUBIC_YARDS;
      setUnit(nextUnit, options);
    }

    function setUnit(nextUnit, options) {
      var silent = options && options.silent;
      var previous = state.unitSystem;
      state.category = isVolumeUnit(nextUnit) ? 'volume' : 'weight';
      state.unitSystem = nextUnit;
      categoryInputs.forEach(function (input) {
        input.checked = input.value === state.category;
      });
      if (volumeUnits) volumeUnits.hidden = state.category !== 'volume';
      if (weightUnits) weightUnits.hidden = state.category !== 'weight';
      unitInputs.forEach(function (input) {
        if (input.value === nextUnit) input.checked = true;
      });
      if (!silent && previous !== nextUnit) {
        quantityInput.value = '';
        state.volumeCapacity = DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS;
        state.usingCustomYards = false;
        clearErrorsAndResults();
      }
      showYardPresets(nextUnit === TRUCK_LOAD_UNITS.CUBIC_YARDS);
      syncUnitLabels();
    }

    function clearErrorsAndResults() {
      quantityError.textContent = '';
      capacityError.textContent = '';
      quantityInput.removeAttribute('aria-invalid');
      capacityInput.removeAttribute('aria-invalid');
      capacitySelect.removeAttribute('aria-invalid');
      results.hidden = true;
      if (status) status.textContent = '';
    }

    function capacityValue() {
      if (currentUnit() === TRUCK_LOAD_UNITS.CUBIC_YARDS && !state.usingCustomYards) {
        return String(state.volumeCapacity);
      }
      return capacityInput.value;
    }

    // Same as the app's Start New Calculation: clear quantity and the result,
    // but keep calculation type, unit, and capacity.
    function startNewCalculation() {
      quantityInput.value = '';
      clearErrorsAndResults();
      quantityInput.focus();
    }

    function calculate(event) {
      if (event) event.preventDefault();
      var quantity = quantityInput.value;
      var capacity = capacityValue();
      var quantityMsg = getInputError(quantity);
      var capacityMsg = getInputError(capacity);
      quantityError.textContent = quantityMsg;
      capacityError.textContent = capacityMsg;
      quantityInput.setAttribute('aria-invalid', quantityMsg ? 'true' : 'false');
      if (currentUnit() === TRUCK_LOAD_UNITS.CUBIC_YARDS && !state.usingCustomYards) {
        capacitySelect.setAttribute('aria-invalid', capacityMsg ? 'true' : 'false');
        capacityInput.removeAttribute('aria-invalid');
      } else {
        capacityInput.setAttribute('aria-invalid', capacityMsg ? 'true' : 'false');
        capacitySelect.removeAttribute('aria-invalid');
      }
      if (quantityMsg || capacityMsg) {
        results.hidden = true;
        if (status) status.textContent = '';
        return null;
      }
      var result = calculateTruckLoadEstimate({
        quantity: quantity,
        capacity: capacity,
        unitSystem: currentUnit(),
      });
      if (!result) {
        results.hidden = true;
        if (status) {
          status.textContent = 'Unable to display this estimate safely. Check quantity and capacity.';
        }
        return null;
      }
      var symbol = unitSymbol(result.unitSystem);
      var loadsText = formatLoadEquivalent(result.exactLoadEquivalent, result.estimatedTrips);
      resultsContext.textContent =
        formatPositiveQuantity(result.quantity) + ' ' + symbol +
        ' · Truck Capacity: ' + formatPositiveQuantity(result.capacity) + ' ' + symbol;
      resultsTrips.textContent = String(result.estimatedTrips);
      resultsLoadsLabel.textContent = loadEquivalentLabel(result.unitSystem);
      resultsLoads.textContent = loadsText || '';
      resultsSafety.textContent = safetyText(result.unitSystem);
      results.hidden = false;
      if (status) status.textContent = '';
      return result;
    }

    categoryInputs.forEach(function (input) {
      input.addEventListener('change', function () {
        setCategory(input.value);
      });
    });
    unitInputs.forEach(function (input) {
      input.addEventListener('change', function () {
        setUnit(input.value);
      });
    });
    if (capacitySelect) {
      capacitySelect.addEventListener('change', function () {
        if (capacitySelect.value === 'custom') {
          state.usingCustomYards = true;
          capacityCustomWrap.hidden = false;
          capacityInput.value = '';
          capacityInput.focus();
        } else {
          state.usingCustomYards = false;
          state.volumeCapacity = Number(capacitySelect.value);
          capacityCustomWrap.hidden = true;
          capacityInput.value = '';
        }
        clearErrorsAndResults();
      });
    }
    quantityInput.addEventListener('input', function () {
      if (results.hidden === false || quantityError.textContent) {
        quantityError.textContent = '';
        quantityInput.removeAttribute('aria-invalid');
        results.hidden = true;
      }
    });
    capacityInput.addEventListener('input', function () {
      if (results.hidden === false || capacityError.textContent) {
        capacityError.textContent = '';
        capacityInput.removeAttribute('aria-invalid');
        results.hidden = true;
      }
    });
    form.addEventListener('submit', calculate);
    root.querySelector('[data-truck-reset]').addEventListener('click', function (event) {
      event.preventDefault();
      startNewCalculation();
    });

    form.removeAttribute('hidden');
    setUnit(TRUCK_LOAD_UNITS.CUBIC_YARDS, { silent: true });

    return { calculate: calculate, startNewCalculation: startNewCalculation, getState: function () { return state; } };
  }

  function autoInit() {
    var root = typeof document !== 'undefined' && document.getElementById('truck-calc');
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
    TRUCK_LOAD_UNITS: TRUCK_LOAD_UNITS,
    YARD_PRESETS: YARD_PRESETS,
    DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS: DEFAULT_TRUCK_CAPACITY_CUBIC_YARDS,
    parsePositiveFiniteNumber: parsePositiveFiniteNumber,
    getInputError: getInputError,
    calculateDecimalTripCount: calculateDecimalTripCount,
    calculateTruckLoadEstimate: calculateTruckLoadEstimate,
    formatPositiveQuantity: formatPositiveQuantity,
    formatLoadEquivalent: formatLoadEquivalent,
    init: init,
  };
});
