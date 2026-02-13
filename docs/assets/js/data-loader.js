/**
 * Data loader for fitness dashboard - loads all static JSON files
 * Fixed version addressing all data display issues
 */

class DataLoader {
    constructor() {
        this.cache = {};
        this.baseUrl = window.location.hostname === 'localhost' ? '' : '/fitness-dashboard';
    }

    async loadJSON(filename) {
        if (this.cache[filename]) {
            return this.cache[filename];
        }

        try {
            const response = await fetch(`${this.baseUrl}/data/${filename}`);
            if (!response.ok) {
                console.error(`Failed to load ${filename}: ${response.status}`);
                return null;
            }
            const data = await response.json();
            this.cache[filename] = data;
            return data;
        } catch (error) {
            console.error(`Error loading ${filename}:`, error);
            return null;
        }
    }

    async loadAll() {
        const [
            activities,
            wellness,
            athlete,
            weeklyTSS,
            ytd,
            heatmap1y,
            heatmap3y,
            meta
        ] = await Promise.all([
            this.loadJSON('activities.json'),
            this.loadJSON('wellness.json'),
            this.loadJSON('athlete.json'),
            this.loadJSON('weekly_tss.json'),
            this.loadJSON('ytd.json'),
            this.loadJSON('heatmap_1y.json'),
            this.loadJSON('heatmap_3y.json'),
            this.loadJSON('meta.json')
        ]);

        return {
            activities: activities || [],
            wellness: wellness || [],
            athlete: athlete || {},
            weeklyTSS: weeklyTSS || [],
            ytd: ytd || {},
            heatmap1y: heatmap1y || {},
            heatmap3y: heatmap3y || {},
            meta: meta || {}
        };
    }

    // Get latest wellness data with all required fields
    latestWellness(wellness) {
        if (!wellness || wellness.length === 0) {
            return {
                ctl: null,
                atl: null,
                tsb: null,
                hrv: null,
                resting_hr: null,
                sleep: null,
                weight: null
            };
        }

        const latest = wellness.slice(-30).reverse(); // Get last 30 days, most recent first
        
        const result = {};
        
        // Find latest non-null value for each metric
        ['ctl', 'atl', 'tsb', 'hrv', 'resting_hr', 'sleep', 'weight'].forEach(field => {
            const entry = latest.find(w => w && w[field] !== null && w[field] !== undefined);
            result[field] = entry ? entry[field] : null;
        });

        return result;
    }

    // Filter activities by type
    getActivitiesByType(activities, types) {
        if (!activities || !Array.isArray(activities)) return [];
        
        const typeArray = Array.isArray(types) ? types : [types];
        return activities.filter(activity => 
            activity && 
            activity.type && 
            typeArray.includes(activity.type) &&
            !activity._note // Filter out Strava stub activities
        );
    }

    // Get cycling activities
    getCyclingActivities(activities) {
        return this.getActivitiesByType(activities, ['Ride', 'VirtualRide']);
    }

    // Get running activities  
    getRunningActivities(activities) {
        return this.getActivitiesByType(activities, ['Run', 'VirtualRun']);
    }

    // Get rowing activities
    getRowingActivities(activities) {
        return this.getActivitiesByType(activities, ['Rowing', 'Row']);
    }

    // Get cardio activities (various cardio types)
    getCardioActivities(activities) {
        const cardioTypes = [
            'Workout', 'CrossTraining', 'Other', 'Elliptical', 
            'StairStepper', 'WeightTraining', 'Yoga'
        ];
        return this.getActivitiesByType(activities, cardioTypes);
    }

    // Calculate activity totals for a date range
    getActivityTotals(activities, days = 90) {
        if (!activities || activities.length === 0) {
            return {
                count: 0,
                distance: 0,
                time: 0,
                elevation: 0,
                tss: 0
            };
        }

        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);

        const recentActivities = activities.filter(a => {
            if (!a || !a.start_date_local) return false;
            const activityDate = new Date(a.start_date_local);
            return activityDate >= cutoff;
        });

        return {
            count: recentActivities.length,
            distance: recentActivities.reduce((sum, a) => sum + (a.distance || 0), 0),
            time: recentActivities.reduce((sum, a) => sum + (a.moving_time || a.elapsed_time || 0), 0),
            elevation: recentActivities.reduce((sum, a) => sum + (a.total_elevation_gain || 0), 0),
            tss: recentActivities.reduce((sum, a) => sum + (a.tss || 0), 0)
        };
    }

    // Get personal bests for specific distances
    getPersonalBests(activities, distances) {
        if (!activities || activities.length === 0) return {};

        const bests = {};
        
        distances.forEach(distance => {
            const distanceKm = distance / 1000; // Convert to km for comparison
            const tolerance = 0.1; // 100m tolerance
            
            const matchingActivities = activities.filter(a => 
                a && 
                a.distance && 
                Math.abs((a.distance / 1000) - distanceKm) <= tolerance &&
                a.moving_time
            );

            if (matchingActivities.length > 0) {
                const fastest = matchingActivities.reduce((best, current) => {
                    const currentPace = current.moving_time / (current.distance / 1000);
                    const bestPace = best.moving_time / (best.distance / 1000);
                    return currentPace < bestPace ? current : best;
                });

                bests[`${distance}m`] = {
                    time: fastest.moving_time,
                    pace: fastest.moving_time / (fastest.distance / 1000),
                    date: fastest.start_date_local,
                    distance: fastest.distance
                };
            }
        });

        return bests;
    }

    // Format time in HH:MM:SS
    formatTime(seconds) {
        if (!seconds || seconds <= 0) return '--:--';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    // Format pace (min/km)
    formatPace(secondsPerKm) {
        if (!secondsPerKm || secondsPerKm <= 0) return '--:--';
        
        const minutes = Math.floor(secondsPerKm / 60);
        const seconds = Math.floor(secondsPerKm % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    // Format distance
    formatDistance(meters) {
        if (!meters || meters <= 0) return '0';
        
        if (meters >= 1000) {
            return `${(meters / 1000).toFixed(1)}km`;
        }
        return `${Math.round(meters)}m`;
    }

    // Get weekly TSS data formatted for charts
    getWeeklyTSSChart(weeklyTSS) {
        if (!weeklyTSS || weeklyTSS.length === 0) return [];

        return weeklyTSS.map(week => ({
            week: week.week,
            date: week.start_date,
            tss: week.tss || 0,
            cycling: week.cycling_tss || 0,
            running: week.running_tss || 0,
            other: (week.tss || 0) - (week.cycling_tss || 0) - (week.running_tss || 0)
        }));
    }

    // Process heatmap data for calendar display
    processHeatmapData(heatmap) {
        if (!heatmap || !heatmap.data) return {};

        const processed = {};
        
        Object.keys(heatmap.data).forEach(date => {
            const dayData = heatmap.data[date];
            if (dayData && dayData.activities && dayData.activities.length > 0) {
                processed[date] = {
                    count: dayData.activities.length,
                    tss: dayData.tss || 0,
                    types: [...new Set(dayData.activities.map(a => a.type))],
                    primaryType: this.getPrimaryActivityType(dayData.activities)
                };
            }
        });

        return processed;
    }

    // Determine primary activity type for a day
    getPrimaryActivityType(activities) {
        if (!activities || activities.length === 0) return null;

        // Priority order: Cycling, Running, Rowing, Other
        const typePriority = {
            'Ride': 1,
            'VirtualRide': 1,
            'Run': 2,
            'VirtualRun': 2,
            'Rowing': 3,
            'Row': 3
        };

        return activities.reduce((primary, activity) => {
            const currentPriority = typePriority[activity.type] || 10;
            const primaryPriority = typePriority[primary?.type] || 10;
            
            return currentPriority < primaryPriority ? activity : primary;
        }).type;
    }

    // Clear cache (useful for development)
    clearCache() {
        this.cache = {};
    }
}

// Global DATA object
window.DATA = new DataLoader();
