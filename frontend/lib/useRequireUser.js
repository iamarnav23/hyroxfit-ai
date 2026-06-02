import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { supabase } from "./supabaseClient";

export default function useRequireUser() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function checkSession() {
      if (!supabase) {
        setIsChecking(false);
        router.replace(`/login?redirect=${encodeURIComponent(router.asPath)}`);
        return;
      }

      const { data } = await supabase.auth.getUser();

      if (!isMounted) {
        return;
      }

      if (!data.user) {
        router.replace(`/login?redirect=${encodeURIComponent(router.asPath)}`);
        setIsChecking(false);
        return;
      }

      setUser(data.user);
      setIsChecking(false);
    }

    checkSession();

    return () => {
      isMounted = false;
    };
  }, [router, router.asPath]);

  return { user, isChecking };
}
