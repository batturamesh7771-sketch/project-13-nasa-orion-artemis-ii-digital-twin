/**
 * NASA Open MCT Custom Telemetry Plugin for Orion Artemis II Digital Twin
 * Connects to the local Open MCT telemetry bridge (ws://localhost:8080/realtime & /history/:id)
 */
function OrionTelemetryPlugin() {
  return function install(openmct) {
    console.log('[Open MCT] Installing NASA Orion Artemis II Telemetry Plugin...');

    // 1. Define custom telemetry object type
    openmct.types.addType('orion.telemetry', {
      name: 'Orion Telemetry Point',
      description: 'Telemetry parameter from NASA Orion Artemis II MPCV Digital Twin',
      cssClass: 'icon-telemetry'
    });

    // 2. Fetch dictionary and register objects
    let dictionaryPromise = fetch('/dictionary.json')
      .then(response => response.json())
      .catch(err => {
        console.error('[Open MCT] Failed to load dictionary.json:', err);
        return { measurements: [] };
      });

    // 3. Register Root Folder
    openmct.objects.addRoot({
      namespace: 'orion.telemetry',
      key: 'root'
    });

    // 4. Object Provider
    const objectProvider = {
      get: function (identifier) {
        return dictionaryPromise.then(dict => {
          if (identifier.key === 'root') {
            return {
              identifier: identifier,
              name: dict.name || 'Orion Artemis II Telemetry',
              type: 'folder',
              location: 'ROOT',
              composition: (dict.measurements || []).map(m => ({
                namespace: 'orion.telemetry',
                key: m.key
              }))
            };
          }

          const measurement = (dict.measurements || []).find(m => m.key === identifier.key);
          if (measurement) {
            return {
              identifier: identifier,
              name: measurement.name,
              type: 'orion.telemetry',
              telemetry: {
                values: [
                  {
                    key: 'value',
                    name: measurement.name,
                    units: measurement.units,
                    format: measurement.format || 'float',
                    min: measurement.min,
                    max: measurement.max,
                    hints: {
                      range: 1
                    }
                  },
                  {
                    key: 'utc',
                    source: 'timestamp',
                    name: 'Timestamp (UTC)',
                    format: 'utc',
                    hints: {
                      domain: 1
                    }
                  },
                  {
                    key: 'met',
                    name: 'Mission Elapsed Time (s)',
                    format: 'number'
                  }
                ]
              },
              location: 'orion.telemetry:root'
            };
          }
          return null;
        });
      }
    };

    openmct.objects.addProvider('orion.telemetry', objectProvider);

    // 5. Realtime WebSocket Subscriber
    const listeners = {};
    let ws = null;
    let reconnectTimeout = null;

    function connectWebSocket() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/realtime`;
      
      try {
        ws = new WebSocket(wsUrl);
      } catch (e) {
        console.warn('[Open MCT] WebSocket initialization error:', e);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
        return;
      }

      ws.onopen = function () {
        console.log('[Open MCT] Connected to Orion Realtime Telemetry WebSocket stream');
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
      };

      ws.onmessage = function (event) {
        try {
          const packet = JSON.parse(event.data);
          // Expect packet format: { id: 'traj.altitude', timestamp: 1775082948000, value: 48.2, met: 48.0 }
          // or an array of such points
          const items = Array.isArray(packet) ? packet : [packet];
          items.forEach(point => {
            if (point && point.id && listeners[point.id]) {
              listeners[point.id].forEach(cb => {
                cb({
                  timestamp: point.timestamp || Date.now(),
                  value: point.value,
                  met: point.met
                });
              });
            }
          });
        } catch (err) {
          console.error('[Open MCT] Error processing incoming telemetry message:', err);
        }
      };

      ws.onclose = function () {
        console.log('[Open MCT] WebSocket disconnected. Reconnecting in 3s...');
        ws = null;
        if (!reconnectTimeout) {
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        }
      };

      ws.onerror = function (err) {
        console.warn('[Open MCT] WebSocket stream warning:', err);
      };
    }

    connectWebSocket();

    // 6. Telemetry Provider (Historical + Realtime)
    const telemetryProvider = {
      supportsRequest: function (domainObject) {
        return domainObject.type === 'orion.telemetry';
      },
      request: function (domainObject, options) {
        const pointId = domainObject.identifier.key;
        let url = `/history/${encodeURIComponent(pointId)}`;
        const params = [];
        if (options && options.start !== undefined) params.push(`start=${options.start}`);
        if (options && options.end !== undefined) params.push(`end=${options.end}`);
        if (params.length > 0) url += `?${params.join('&')}`;

        return fetch(url)
          .then(res => res.json())
          .then(data => {
            if (Array.isArray(data)) {
              return data.map(d => ({
                timestamp: d.timestamp,
                value: d.value,
                met: d.met
              }));
            }
            return [];
          })
          .catch(err => {
            console.error(`[Open MCT] Historical telemetry request failed for ${pointId}:`, err);
            return [];
          });
      },
      supportsSubscribe: function (domainObject) {
        return domainObject.type === 'orion.telemetry';
      },
      subscribe: function (domainObject, callback) {
        const pointId = domainObject.identifier.key;
        if (!listeners[pointId]) {
          listeners[pointId] = [];
        }
        listeners[pointId].push(callback);

        return function unsubscribe() {
          listeners[pointId] = listeners[pointId].filter(cb => cb !== callback);
        };
      }
    };

    openmct.telemetry.addProvider(telemetryProvider);

    // 7. Limit Evaluator for Caution (Yellow) and Alarm (Red)
    dictionaryPromise.then(dict => {
      const measurementMap = {};
      (dict.measurements || []).forEach(m => {
        measurementMap[m.key] = m;
      });

      if (typeof openmct.telemetry.addLimitEvaluator === 'function') {
        openmct.telemetry.addLimitEvaluator({
        supportsLimit: function (domainObject) {
          return domainObject.type === 'orion.telemetry';
        },
        evaluate: function (datum, valueMetadata) {
          if (!datum || datum.value === undefined) return;
          const pointId = valueMetadata && valueMetadata.key === 'value' ? (datum.id || (datum.pointId)) : null;
          
          // Fallback search across known measurement limits
          let limits = null;
          if (pointId && measurementMap[pointId]) {
            limits = measurementMap[pointId].limits;
          } else {
            // Find which measurement matches this value range/domain
            for (let k in measurementMap) {
              if (measurementMap[k].name === valueMetadata.name) {
                limits = measurementMap[k].limits;
                break;
              }
            }
          }

          if (!limits) return;

          const val = Number(datum.value);

          // Check Red Alarm first
          if (limits.red) {
            if (limits.red.high !== undefined && val >= limits.red.high) {
              return {
                cssClass: 'is-limit--red',
                name: 'CRITICAL HIGH ALARM',
                level: 2
              };
            }
            if (limits.red.low !== undefined && val <= limits.red.low) {
              return {
                cssClass: 'is-limit--red',
                name: 'CRITICAL LOW ALARM',
                level: 2
              };
            }
          }

          // Check Yellow Caution
          if (limits.yellow) {
            if (limits.yellow.high !== undefined && val >= limits.yellow.high) {
              return {
                cssClass: 'is-limit--yellow',
                name: 'CAUTION HIGH',
                level: 1
              };
            }
            if (limits.yellow.low !== undefined && val <= limits.yellow.low) {
              return {
                cssClass: 'is-limit--yellow',
                name: 'CAUTION LOW',
                level: 1
              };
            }
          }
        }
      });
      }
    });

    console.log('[Open MCT] NASA Orion Artemis II Telemetry Plugin registered successfully.');
  };
}
