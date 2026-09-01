import { Stack } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useEffect } from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';

export default function RootLayout() {
  const { token, hydrate, isHydrated } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (!isHydrated) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#8b5cf6" />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      {token ? (
        <>
          <Stack.Screen name="/dashboard" options={{ title: 'Dashboard' }} />
          <Stack.Screen name="/dashboard/projects" options={{ title: 'Projects' }} />
          <Stack.Screen name="/dashboard/episodes" options={{ title: 'Episodes' }} />
          <Stack.Screen name="/dashboard/settings" options={{ title: 'Settings' }} />
        </>
      ) : (
        <>
          <Stack.Screen name="/auth/login" options={{ title: 'Login' }} />
          <Stack.Screen name="/auth/register" options={{ title: 'Register' }} />
        </>
      )}
    </Stack>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1e293b',
  },
});